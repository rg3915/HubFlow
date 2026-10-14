from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.errors import HttpError

from hubflow.accounts.schemas import DetailOut
from hubflow.projects.models import Project

from .mentions import notify_mentions
from .models import Card, ChecklistItem, Column, Comment, Label
from .schemas import (
    BoardOut,
    CardIn,
    CardLabelsIn,
    CardMoveOut,
    CardOut,
    ChecklistItemIn,
    ChecklistItemOut,
    ChecklistOrderIn,
    CommentIn,
    CommentOut,
    LabelIn,
    LabelOut,
    MoveIn,
)
from .services import card_queryset, create_card, delete_card, move_card, renumber, resolve_assignee, start_card

router = Router(tags=['boards'])


@router.post('/projects/{project_id}/cards', response={201: CardOut})
def add_card(request, project_id: int, data: CardIn):
    project = get_object_or_404(Project, id=project_id)
    fields = data.dict(exclude={'assignee_id'}) | {'assignee': resolve_assignee(data.assignee_id)}
    return Status(201, create_card(project, user=request.user, **fields))


@router.get('/projects/{project_id}/board', response=BoardOut)
def board(request, project_id: int, archived: bool = False):
    project = get_object_or_404(Project.objects.select_related('client'), id=project_id)
    cards = card_queryset().filter(project=project).order_by('position', 'id')
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
    return get_object_or_404(card_queryset(), id=card_id)


@router.put('/cards/{card_id}', response=CardOut)
def update_card(request, card_id: int, data: CardIn):
    card = get_object_or_404(Card, id=card_id)
    card.title, card.description, card.due_date = data.title, data.description, data.due_date
    card.assignee = resolve_assignee(data.assignee_id)
    card.save(update_fields=['title', 'description', 'due_date', 'assignee', 'modified'])
    return card


@router.delete('/cards/{card_id}', response={204: None})
def remove_card(request, card_id: int):
    delete_card(get_object_or_404(Card, id=card_id))
    return Status(204, None)


@router.post('/cards/{card_id}/archive', response=CardOut)
def archive(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    return move_card(card, Column.ARCHIVED, user=request.user)


@router.get('/cards/{card_id}/comments', response=list[CommentOut])
def list_comments(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    return card.comments.select_related('author').prefetch_related('mentions')


@router.post('/cards/{card_id}/comments', response={201: CommentOut})
def add_comment(request, card_id: int, data: CommentIn):
    card = get_object_or_404(Card.objects.select_related('project__client'), id=card_id)
    comment = Comment.objects.create(card=card, author=request.user, text=data.text)
    notify_mentions(comment)
    return Status(201, comment)


def own_comment_or_403(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related('author'), id=comment_id)
    if comment.author_id != request.user.id:
        raise HttpError(403, 'Só o autor pode alterar este comentário.')
    return comment


@router.put('/comments/{comment_id}', response=CommentOut)
def update_comment(request, comment_id: int, data: CommentIn):
    comment = own_comment_or_403(request, comment_id)
    comment.text = data.text
    comment.save(update_fields=['text', 'modified'])
    notify_mentions(comment)
    return comment


@router.delete('/comments/{comment_id}', response={204: None})
def delete_comment(request, comment_id: int):
    own_comment_or_403(request, comment_id).delete()
    return Status(204, None)


def label_name_taken(project_id, name, exclude_id=None):
    return Label.objects.filter(project_id=project_id, name__iexact=name).exclude(id=exclude_id).exists()


@router.get('/projects/{project_id}/labels', response=list[LabelOut])
def list_labels(request, project_id: int):
    return get_object_or_404(Project, id=project_id).labels.all()


@router.post('/projects/{project_id}/labels', response={201: LabelOut, 400: DetailOut})
def add_label(request, project_id: int, data: LabelIn):
    project = get_object_or_404(Project, id=project_id)
    if label_name_taken(project.id, data.name):
        return Status(400, {'detail': 'Já existe uma etiqueta com este nome no projeto.'})
    return Status(201, Label.objects.create(project=project, **data.dict()))


@router.put('/labels/{label_id}', response={200: LabelOut, 400: DetailOut})
def update_label(request, label_id: int, data: LabelIn):
    label = get_object_or_404(Label, id=label_id)
    if label_name_taken(label.project_id, data.name, exclude_id=label.id):
        return Status(400, {'detail': 'Já existe uma etiqueta com este nome no projeto.'})
    label.name, label.color = data.name, data.color
    label.save()
    return label


@router.delete('/labels/{label_id}', response={204: None})
def delete_label(request, label_id: int):
    get_object_or_404(Label, id=label_id).delete()
    return Status(204, None)


@router.put('/cards/{card_id}/labels', response={200: CardOut, 400: DetailOut})
def set_card_labels(request, card_id: int, data: CardLabelsIn):
    card = get_object_or_404(Card, id=card_id)
    labels = Label.objects.filter(id__in=data.label_ids)
    if labels.exclude(project_id=card.project_id).exists() or labels.count() != len(set(data.label_ids)):
        return Status(400, {'detail': 'Use só etiquetas deste projeto.'})
    card.labels.set(labels)
    return card


@router.get('/cards/{card_id}/checklist', response=list[ChecklistItemOut])
def list_checklist(request, card_id: int):
    return get_object_or_404(Card, id=card_id).checklist_items.all()


@router.post('/cards/{card_id}/checklist', response={201: ChecklistItemOut})
def add_checklist_item(request, card_id: int, data: ChecklistItemIn):
    card = get_object_or_404(Card, id=card_id)
    position = card.checklist_items.count()
    return Status(201, ChecklistItem.objects.create(card=card, position=position, **data.dict()))


@router.put('/checklist/{item_id}', response=ChecklistItemOut)
def update_checklist_item(request, item_id: int, data: ChecklistItemIn):
    item = get_object_or_404(ChecklistItem, id=item_id)
    item.text, item.done = data.text, data.done
    item.save(update_fields=['text', 'done'])
    return item


@router.delete('/checklist/{item_id}', response={204: None})
def delete_checklist_item(request, item_id: int):
    item = get_object_or_404(ChecklistItem, id=item_id)
    card_id = item.card_id
    item.delete()
    renumber(list(ChecklistItem.objects.filter(card_id=card_id)))
    return Status(204, None)


@router.put('/cards/{card_id}/checklist/order', response={200: list[ChecklistItemOut], 400: DetailOut})
def reorder_checklist(request, card_id: int, data: ChecklistOrderIn):
    card = get_object_or_404(Card, id=card_id)
    items = {item.id: item for item in card.checklist_items.all()}
    if set(data.item_ids) != set(items) or len(data.item_ids) != len(items):
        return Status(400, {'detail': 'Informe todos os itens deste card, uma vez cada.'})
    ordered = [items[item_id] for item_id in data.item_ids]
    renumber(ordered)
    return ordered
