from django.contrib.auth import get_user_model
from django.db.models import Q
from ninja import Query, Router

from hubflow.boards.models import Card, Column, Label
from hubflow.clients.models import Client
from hubflow.projects.models import Project

from .schemas import SearchOut

router = Router(tags=['search'])

LIMIT = 10
# "em desenvolvimento" → doing, "concluído" → done...; a chave em inglês também vale.
COLUMN_BY_NAME = {label.lower(): key for key, label in Column.choices} | {key: key for key in Column.values}


def search_cards(q):
    cards = Card.objects.select_related('project__client').order_by('-modified')
    column = COLUMN_BY_NAME.get(q.lower())
    if column:
        return cards.filter(column=column)
    match = Q(title__icontains=q) | Q(description__icontains=q)
    if q.startswith('#') and q[1:].isdigit():
        match |= Q(number=int(q[1:]))
    return cards.filter(match)


@router.get('', response=SearchOut)
def search(request, q: str = Query(..., min_length=2)):
    """Busca global: uma consulta por tipo, no máximo 10 itens cada."""
    users = get_user_model().objects.filter(is_active=True).filter(Q(email__icontains=q) | Q(name__icontains=q))
    return {
        'cards': list(search_cards(q)[:LIMIT]),
        'projects': list(Project.objects.select_related('client').filter(name__icontains=q)[:LIMIT]),
        'clients': list(Client.objects.filter(name__icontains=q)[:LIMIT]),
        'users': list(users.order_by('name', 'email')[:LIMIT]),
        'labels': list(Label.objects.filter(name__icontains=q).order_by('name', 'project_id')[:LIMIT]),
    }
