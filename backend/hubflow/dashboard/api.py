from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from ninja import Router

from hubflow.boards.models import Card, CardEvent, CardMove, Column, Comment
from hubflow.boards.services import card_queryset
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry
from hubflow.timetracking.services import project_median_estimate

from .schemas import ActivityItemOut, DeadlinesOut, OverviewOut

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
