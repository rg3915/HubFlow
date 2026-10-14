"""Avisos ao vivo do quadro: a API chama estas funções depois de cada mudança de card."""

from .events import publish


def _by(user):
    return user.email if user is not None and getattr(user, 'email', None) else None


def card_payload(card):
    # Import local: boards importa realtime, e vice-versa.
    from hubflow.boards.schemas import CardOut
    from hubflow.boards.services import card_queryset

    fresh = card_queryset().get(id=card.id)
    fresh.project_median = getattr(card, 'project_median', None)
    return CardOut.from_orm(fresh).dict()


def card_created(card, user=None):
    publish(card.project_id, 'card_created', {'card': card_payload(card), 'by': _by(user)})


def card_updated(card, user=None):
    publish(card.project_id, 'card_updated', {'card': card_payload(card), 'by': _by(user)})


def card_moved(card, from_column, to_column, user=None):
    data = {'card_id': card.id, 'from_column': from_column, 'to_column': to_column, 'position': card.position}
    publish(card.project_id, 'card_moved', data | {'by': _by(user)})


def card_deleted(project_id, card_id, user=None):
    publish(project_id, 'card_deleted', {'card_id': card_id, 'by': _by(user)})
