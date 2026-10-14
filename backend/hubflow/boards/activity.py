from .models import CardEvent


def record(card, kind, user=None, **data):
    return CardEvent.objects.create(card=card, kind=kind, user=user, data=data)


def card_activity(card):
    """Linha do tempo do card: uma consulta por tipo, unidas e ordenadas em memória (sem N+1)."""
    items = []
    for event in card.events.select_related('user'):
        items.append(_item(event.kind, event.user, event.data, event.created, event.id))
    for move in card.moves.select_related('user'):
        data = {'from_column': move.from_column, 'to_column': move.to_column}
        items.append(_item('moved', move.user, data, move.created, move.id))
    for comment in card.comments.select_related('author'):
        items.append(_item('comment', comment.author, {'text': comment.text}, comment.created, comment.id))
    for att in card.attachments.select_related('uploaded_by'):
        items.append(_item('attachment', att.uploaded_by, {'name': att.name}, att.created, att.id))
    return sorted(items, key=lambda item: (item['created'], item['_id']), reverse=True)


def _item(kind, user, data, created, item_id):
    return {'kind': kind, 'user': user, 'data': data, 'created': created, '_id': item_id}


def record_card_changes(card, user, before):
    """Registra o que mudou entre `before` (dict) e o card salvo."""
    if before['assignee_id'] != card.assignee_id:
        record(card, 'assignee', user, assignee=card.assignee.email if card.assignee else None)
    if before['due_date'] != card.due_date:
        record(card, 'due_date', user, due_date=card.due_date.isoformat() if card.due_date else None)


def record_labels(card, user):
    record(card, 'labels', user, labels=[label.name for label in card.labels.all()])
