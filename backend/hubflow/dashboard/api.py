from datetime import timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import Extract, TruncDate
from django.utils import timezone
from ninja import Router

from hubflow.boards.models import Card, CardEvent, CardMove, Column, Comment
from hubflow.boards.services import card_queryset
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry
from hubflow.timetracking.services import project_median_estimate

from .schemas import ActivityItemOut, DeadlinesOut, HeatmapOut, OverviewOut, WeekOut

router = Router(tags=['dashboard'])

OPEN_COLUMNS = (Column.BACKLOG, Column.SPRINT, Column.DOING, Column.QA)


@router.get('', response=OverviewOut)
def overview(request):
    """Visão geral de todos os projetos ativos, agregada em poucas consultas."""
    active_cards = Card.objects.filter(project__is_active=True)
    counts = dict(active_cards.values_list('column').annotate(n=Count('id')).values_list('column', 'n'))

    in_progress = list(
        card_queryset()
        .filter(project__is_active=True, column=Column.DOING)
        .select_related('project__client')
        .order_by('project__client__name', 'project__name', 'position')
    )
    medians = {}
    for card in in_progress:  # RN-75: uma mediana por projeto, não por card
        medians.setdefault(card.project_id, project_median_estimate(card.project_id))
        card.project_median = medians[card.project_id]

    running = list(
        TimeEntry.objects.filter(ended_at__isnull=True, card__project__is_active=True)
        .select_related('card__project', 'user')
        .order_by('started_at')
    )
    for entry in running:
        entry.mine = entry.user_id == request.user.id

    return {
        'by_column': [{'key': key, 'label': label, 'count': counts.get(key, 0)} for key, label in Column.choices],
        'in_progress': in_progress,
        'running_timers': running,
        'totals': {
            'clients': Client.objects.filter(is_active=True).count(),
            'projects': Project.objects.filter(is_active=True).count(),
            'open_cards': active_cards.filter(column__in=OPEN_COLUMNS).count(),
            'running_timers': len(running),
        },
    }


def _activity_item(kind, card, user, data, created):
    return {
        'kind': kind,
        'card_id': card.id,
        'card_number': card.number,
        'card_title': card.title,
        'project_id': card.project_id,
        'project_name': card.project.name,
        'user': user,
        'data': data,
        'created': created,
    }


@router.get('/activity', response=list[ActivityItemOut])
def activity(request, limit: int = 20):
    """Últimos cards criados, movidos, comentados e tempos registrados: uma consulta por tipo, unidas em memória."""
    active = {'card__project__is_active': True}
    recent = lambda qs, field='-created': qs.filter(**active).order_by(field)[:limit]  # noqa: E731
    items = []
    for event in recent(CardEvent.objects.filter(kind='created').select_related('card__project', 'user')):
        items.append(_activity_item('created', event.card, event.user, {}, event.created))
    for move in recent(CardMove.objects.select_related('card__project', 'user')):
        data = {'from_column': move.from_column, 'to_column': move.to_column}
        items.append(_activity_item('moved', move.card, move.user, data, move.created))
    for comment in recent(Comment.objects.select_related('card__project', 'author')):
        text = {'text': comment.text[:120]}
        items.append(_activity_item('comment', comment.card, comment.author, text, comment.created))
    for entry in recent(
        TimeEntry.objects.filter(ended_at__isnull=False).select_related('card__project', 'user'), '-ended_at'
    ):
        items.append(_activity_item('time', entry.card, entry.user, {'hours': round(entry.hours, 2)}, entry.ended_at))
    items.sort(key=lambda item: item['created'], reverse=True)
    return items[:limit]


@router.get('/deadlines', response=DeadlinesOut)
def deadlines(request, days: int = 7):
    """Cards vencidos e vencendo nos próximos `days` dias (RN-46), só em projetos ativos."""
    today = timezone.localdate()
    pending = (
        card_queryset()
        .filter(project__is_active=True, due_date__isnull=False)
        .exclude(column__in=(Column.DONE, Column.ARCHIVED))
        .select_related('project__client')
        .order_by('due_date', 'id')
    )
    return {
        'overdue': list(pending.filter(due_date__lt=today)),
        'upcoming': list(pending.filter(due_date__gte=today, due_date__lte=today + timedelta(days=days))),
    }


HEATMAP_WEEKS = 26
LEVELS = (1, 3, 5)  # limites em horas/dia: até 1h, até 3h, até 5h, mais que 5h


def level(hours):
    if hours <= 0:
        return 0
    return 1 + sum(hours > limit for limit in LEVELS)


def hours_by(entries, *group_fields, **annotations):
    """Soma de horas das entradas fechadas agrupada pelos campos pedidos (uma consulta)."""
    rows = (
        entries.filter(ended_at__isnull=False)
        .annotate(**annotations)
        .values(*group_fields)
        .annotate(seconds=Extract(Sum(F('ended_at') - F('started_at')), 'epoch'))
    )
    return [{**row, 'hours': round(row['seconds'] / 3600, 2)} for row in rows]


@router.get('/heatmap', response=HeatmapOut)
def heatmap(request, project: int | None = None):
    """Horas por dia nas últimas 26 semanas (estilo GitHub), com nível 0–4."""
    today = timezone.localdate()
    first = today - timedelta(days=HEATMAP_WEEKS * 7 - 1)
    entries = TimeEntry.objects.filter(started_at__date__gte=first, started_at__date__lte=today)
    if project:
        entries = entries.filter(card__project_id=project)
    by_day = {row['day']: row['hours'] for row in hours_by(entries, 'day', day=TruncDate('started_at'))}
    days = [first + timedelta(days=i) for i in range(HEATMAP_WEEKS * 7)]
    return {
        'weeks': HEATMAP_WEEKS,
        'days': [{'date': d, 'hours': by_day.get(d, 0.0), 'level': level(by_day.get(d, 0.0))} for d in days],
        'total_hours': round(sum(by_day.values()), 2),
    }


@router.get('/week', response=WeekOut)
def week(request):
    """Horas da semana corrente (segunda a domingo) por projeto."""
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    entries = TimeEntry.objects.filter(started_at__date__gte=start, started_at__date__lte=end)
    rows = hours_by(
        entries,
        'project_id',
        'project_name',
        'client_name',
        project_id=F('card__project_id'),
        project_name=F('card__project__name'),
        client_name=F('card__project__client__name'),
    )
    rows.sort(key=lambda row: (-row['hours'], row['project_name']))
    return {'start': start, 'end': end, 'total_hours': round(sum(r['hours'] for r in rows), 2), 'by_project': rows}
