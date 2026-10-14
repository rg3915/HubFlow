"""Verificação periódica: SLA estourado (gatilho das automações) e prazos vencidos (aviso no sino). RN-111/112."""

from datetime import timedelta

from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from hubflow.boards.activity import record
from hubflow.boards.models import Card, Column
from hubflow.boards.notifications import notify_in_app

from . import engine
from .models import ColumnSla

OPEN = {'column__in': [Column.DONE, Column.ARCHIVED]}


def breached_sla_cards(now):
    hours = ColumnSla.objects.filter(project=OuterRef('project_id'), column=OuterRef('column')).values('hours')[:1]
    candidates = (
        Card.objects.filter(sla_breached_at__isnull=True)
        .exclude(**OPEN)
        .annotate(sla_hours=Subquery(hours))
        .filter(sla_hours__isnull=False)
    )
    return [card for card in candidates if now > card.column_entered_at + timedelta(hours=card.sla_hours)]


def check_deadlines_and_sla(now=None):
    """Dispara cada SLA estourado uma vez por card/coluna e avisa o responsável de prazo vencido uma vez por prazo."""
    now = now or timezone.now()
    late = breached_sla_cards(now)
    for card in late:
        card.sla_breached_at = now
        card.save(update_fields=['sla_breached_at', 'modified'])
        record(card, 'sla_breached', None, column=card.column, hours=card.sla_hours)
        engine.run('sla_breached', card, card.column)

    overdue = list(
        Card.objects.filter(due_date__lt=timezone.localdate(now), assignee__isnull=False)
        .exclude(**OPEN)
        .exclude(due_notified_on=F('due_date'))
        .select_related('assignee')
    )
    for card in overdue:
        when = card.due_date.strftime('%d/%m')
        notify_in_app([card.assignee], 'overdue', card, f'Prazo vencido em {when}: #{card.number} {card.title}')
        card.due_notified_on = card.due_date
    Card.objects.bulk_update(overdue, ['due_notified_on'])
    return {'sla': len(late), 'overdue': len(overdue)}
