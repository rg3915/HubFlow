from django.db.models import Count
from ninja import Router

from hubflow.boards.models import Card, Column
from hubflow.boards.services import card_queryset
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry
from hubflow.timetracking.services import project_median_estimate

from .schemas import OverviewOut

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
