from django.db import transaction

from .models import Card, Column


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
    card.column = column
    renumber(target)
    if source is not target:
        renumber(source)
    card.save(update_fields=['column', 'modified'])
    return card


def start_card(card, user=None):
    # RN-36
    return move_card(card, Column.DOING, user=user)
