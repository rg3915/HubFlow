from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import File, Router, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile

from hubflow.accounts.schemas import DetailOut
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint
from hubflow.timetracking.services import project_median_estimate

from .activity import card_activity, record_card_changes, record_labels
from .mentions import notify_mentions
from .models import Attachment, Card, ChecklistItem, Column, Comment, Label
from .schemas import (
    ActivityOut,
    AttachmentOut,
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
from .services import (
    card_queryset,
    create_card,
    delete_card,
    move_card,
    renumber,
    resolve_assignee,
    start_card,
    sync_issue_fields,
)

router = Router(tags=['boards'])


@router.post('/projects/{project_id}/cards', response={201: CardOut, 400: DetailOut})
def add_card(request, project_id: int, data: CardIn):
    project = get_object_or_404(Project, id=project_id)
    sprint = project_sprint_or_400(project.id, data.sprint_id)
    if isinstance(sprint, Status):
        return sprint
    fields = data.dict(exclude={'assignee_id', 'sprint_id'}) | {'assignee': resolve_assignee(data.assignee_id)}
    return Status(201, create_card(project, user=request.user, sprint=sprint, **fields))


def project_sprint_or_400(project_id, sprint_id):
    """Sprint do próprio projeto, None quando não informada, ou a resposta 400."""
    if sprint_id is None:
        return None
    sprint = Sprint.objects.filter(id=sprint_id, project_id=project_id).first()
    return sprint or Status(400, {'detail': 'Use uma sprint deste projeto.'})


@router.get('/projects/{project_id}/board', response=BoardOut)
def board(request, project_id: int, archived: bool = False, sprint: int | None = None):
    project = get_object_or_404(Project.objects.select_related('client'), id=project_id)
    cards = card_queryset().filter(project=project).order_by('position', 'id')
    if sprint is not None:
        cards = cards.filter(sprint_id=sprint)
    if not archived:  # RN-37
        cards = cards.exclude(column=Column.ARCHIVED)
    # Uma consulta só; o agrupamento por coluna é feito em memória.
    median = project_median_estimate(project.id)  # RN-75: uma vez por quadro
    by_column = {key: [] for key in Column.values}
    for card in cards:
        card.project_median = median
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


@router.put('/cards/{card_id}', response={200: CardOut, 400: DetailOut})
def update_card(request, card_id: int, data: CardIn):
    card = get_object_or_404(Card, id=card_id)
    before = {'assignee_id': card.assignee_id, 'due_date': card.due_date}
    card.title, card.description, card.due_date = data.title, data.description, data.due_date
    card.estimate_hours = data.estimate_hours
    card.assignee = resolve_assignee(data.assignee_id)
    if data.sprint_id is not None:
        sprint = project_sprint_or_400(card.project_id, data.sprint_id)
        if isinstance(sprint, Status):
            return sprint
        card.sprint = sprint
    card.save(update_fields=['title', 'description', 'due_date', 'estimate_hours', 'assignee', 'sprint', 'modified'])
    record_card_changes(card, request.user, before)
    sync_issue_fields(card)
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
    record_labels(card, request.user)
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


@router.get('/cards/{card_id}/attachments', response=list[AttachmentOut])
def list_attachments(request, card_id: int):
    return get_object_or_404(Card, id=card_id).attachments.select_related('uploaded_by')


@router.post('/cards/{card_id}/attachments', response={201: AttachmentOut, 400: DetailOut})
def add_attachment(request, card_id: int, file: UploadedFile = File(...)):
    card = get_object_or_404(Card, id=card_id)
    limit = settings.ATTACHMENT_MAX_BYTES
    if file.size > limit:
        return Status(400, {'detail': f'Arquivo grande demais. O tamanho máximo é {limit / 1024 / 1024:.0f} MB.'})
    attachment = Attachment(card=card, name=file.name, size=file.size, uploaded_by=request.user)
    attachment.file.save(file.name, file, save=True)
    return Status(201, attachment)


@router.delete('/attachments/{attachment_id}', response={204: None})
def delete_attachment(request, attachment_id: int):
    attachment = get_object_or_404(Attachment, id=attachment_id)
    if attachment.uploaded_by_id != request.user.id:
        raise HttpError(403, 'Só quem enviou o anexo pode excluí-lo.')
    attachment.file.delete(save=False)
    attachment.delete()
    return Status(204, None)


@router.get('/cards/{card_id}/activity', response=list[ActivityOut])
def activity(request, card_id: int):
    return card_activity(get_object_or_404(Card, id=card_id))
