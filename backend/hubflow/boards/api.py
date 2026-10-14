from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.projects.models import Project

from .models import Card, Column
from .schemas import BoardOut, CardIn, CardOut

router = Router(tags=['boards'])


@router.post('/projects/{project_id}/cards', response={201: CardOut})
def create_card(request, project_id: int, data: CardIn):
    project = get_object_or_404(Project, id=project_id)
    card = Card.objects.create(project=project, created_by=request.user, **data.dict())
    return Status(201, card)


@router.get('/projects/{project_id}/board', response=BoardOut)
def board(request, project_id: int, archived: bool = False):
    project = get_object_or_404(Project.objects.select_related('client'), id=project_id)
    cards = project.cards.order_by('position', 'id')
    if not archived:  # RN-37
        cards = cards.exclude(column=Column.ARCHIVED)
    # Uma consulta só; o agrupamento por coluna é feito em memória.
    by_column = {key: [] for key in Column.values}
    for card in cards:
        by_column[card.column].append(card)
    return {
        'project': {'id': project.id, 'name': project.name, 'client_name': project.client.name},
        'columns': [{'key': key, 'label': label, 'cards': by_column[key]} for key, label in Column.choices],
    }
