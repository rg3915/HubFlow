from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.projects.models import Project

from .models import Card, Column
from .schemas import BoardOut, CardIn, CardMoveOut, CardOut, MoveIn
from .services import create_card, delete_card, move_card, start_card

router = Router(tags=['boards'])


@router.post('/projects/{project_id}/cards', response={201: CardOut})
def add_card(request, project_id: int, data: CardIn):
    project = get_object_or_404(Project, id=project_id)
    return Status(201, create_card(project, user=request.user, **data.dict()))


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


@router.post('/cards/{card_id}/move', response=CardOut)
def move(request, card_id: int, data: MoveIn):
    card = get_object_or_404(Card, id=card_id)
    return move_card(card, data.column, data.position, user=request.user)


@router.post('/cards/{card_id}/start', response=CardOut)
def start(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    return start_card(card, user=request.user)


@router.get('/cards/{card_id}/history', response=list[CardMoveOut])
def history(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    return card.moves.select_related('user')


@router.get('/cards/{card_id}', response=CardOut)
def get_card(request, card_id: int):
    return get_object_or_404(Card, id=card_id)


@router.put('/cards/{card_id}', response=CardOut)
def update_card(request, card_id: int, data: CardIn):
    card = get_object_or_404(Card, id=card_id)
    card.title, card.description = data.title, data.description
    card.save(update_fields=['title', 'description', 'modified'])
    return card


@router.delete('/cards/{card_id}', response={204: None})
def remove_card(request, card_id: int):
    delete_card(get_object_or_404(Card, id=card_id))
    return Status(204, None)


@router.post('/cards/{card_id}/archive', response=CardOut)
def archive(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    return move_card(card, Column.ARCHIVED, user=request.user)
