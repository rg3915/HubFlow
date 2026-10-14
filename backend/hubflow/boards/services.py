from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Card, CardMove, Column
from .notifications import notify


def create_card(project, user=None, **data):
    """Cria o card no Backlog (RN-31) e avisa os destinatários."""
    card = Card.objects.create(project=project, created_by=user, **data)
    notify('created', card)
    return card


def resolve_assignee(assignee_id):
    """Devolve o usuário responsável ou 404; None quando o card fica sem responsável."""
    if assignee_id is None:
        return None
    return get_object_or_404(get_user_model(), id=assignee_id, is_active=True)


def renumber(cards):
    """Deixa as posições consecutivas a partir de 0, na ordem recebida (RN-33)."""
    for index, card in enumerate(cards):
        card.position = index
    Card.objects.bulk_update(cards, ['position'])


@transaction.atomic
def move_card(card, column, position=None, user=None):
    """Move o card para a coluna/posição e reordena origem e destino (RN-33, RN-34).

    É o único caminho para mudar a coluna de um card: API, CLI e automações passam por aqui.
    """
    siblings = Card.objects.select_for_update().filter(project_id=card.project_id).exclude(id=card.id)
    source = list(siblings.filter(column=card.column).order_by('position', 'id'))
    target = source if column == card.column else list(siblings.filter(column=column).order_by('position', 'id'))

    position = len(target) if position is None else max(0, min(position, len(target)))
    target.insert(position, card)
    from_column = card.column
    if column != from_column:
        CardMove.objects.create(card=card, from_column=from_column, to_column=column, user=user)
    card.column = column
    renumber(target)
    if source is not target:
        renumber(source)
    card.save(update_fields=['column', 'modified'])
    if column == Column.DONE:
        notify('done', card)
    elif column not in (from_column, Column.ARCHIVED):
        notify('moved', card, from_column=from_column, to_column=column)
    return card


def start_card(card, user=None):
    # RN-36
    return move_card(card, Column.DOING, user=user)


@transaction.atomic
def delete_card(card):
    """Exclui o card e fecha o buraco na coluna (RN-33)."""
    column, project_id = card.column, card.project_id
    card.delete()
    renumber(list(Card.objects.filter(project_id=project_id, column=column).order_by('position', 'id')))


@transaction.atomic
def archive_project(project, user=None):
    """RN-24: excluir um projeto arquiva os cards e desativa o projeto, sem apagar nada."""
    for card in project.cards.exclude(column=Column.ARCHIVED).order_by('column', 'position'):
        move_card(card, Column.ARCHIVED, user=user)
    project.is_active = False
    project.save(update_fields=['is_active', 'modified'])
