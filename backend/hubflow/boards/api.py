from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Case, F, Value, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import File, Router, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile

from hubflow.accounts.schemas import DetailOut
from hubflow.dashboard.schemas import DashboardCardOut
from hubflow.permissions.services import (
    has_perm,
    require,
    require_card_delete,
    require_card_edit,
    visible_in_project_or_404,
    visible_project_or_404,
    visible_projects,
)
from hubflow.realtime import broadcast
from hubflow.sprints.models import Sprint
from hubflow.timetracking.services import project_median_estimate

from .activity import card_activity, record, record_card_changes, record_labels
from .mentions import notify_mentions
from .models import Attachment, Card, ChecklistItem, Column, Comment, CustomField, Label, Notification
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
    CustomFieldIn,
    CustomFieldOut,
    LabelIn,
    LabelOut,
    MoveIn,
    NotificationsOut,
    OrderIn,
)
from .services import (
    card_queryset,
    create_card,
    delete_card,
    merge_custom_values,
    move_card,
    renumber,
    resolve_assignee,
    start_card,
    sync_issue_fields,
)

router = Router(tags=['boards'])


def visible_card(request, card_id, queryset=None):
    """Card de um projeto que a pessoa pode ver (404 caso contrário)."""
    cards = (queryset or Card.objects).filter(project__in=visible_projects(request.user))
    return get_object_or_404(cards, id=card_id)


@router.post('/projects/{project_id}/cards', response={201: CardOut, 400: DetailOut})
def add_card(request, project_id: int, data: CardIn):
    require(request.user, 'boards.add_card')
    project = get_object_or_404(visible_projects(request.user), id=project_id)
    sprint = project_sprint_or_400(project.id, data.sprint_id)
    if isinstance(sprint, Status):
        return sprint
    try:
        values, _ = merge_custom_values(project, {}, data.fields, creating=True)
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    fields = data.dict(exclude={'assignee_id', 'sprint_id', 'fields'}) | {
        'assignee': resolve_assignee(data.assignee_id)
    }
    card = create_card(project, user=request.user, sprint=sprint, custom_values=values, **fields)
    return Status(201, card)


def project_sprint_or_400(project_id, sprint_id):
    """Sprint do próprio projeto, None quando não informada, ou a resposta 400."""
    if sprint_id is None:
        return None
    sprint = Sprint.objects.filter(id=sprint_id, project_id=project_id).first()
    return sprint or Status(400, {'detail': 'Use uma sprint deste projeto.'})


@router.get('/projects/{project_id}/board', response=BoardOut)
def board(request, project_id: int, archived: bool = False, sprint: int | None = None):
    project = get_object_or_404(visible_projects(request.user), id=project_id)
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
    card = visible_card(request, card_id)
    require_card_edit(request.user, card)
    return move_card(card, data.column, data.position, user=request.user)


@router.post('/cards/{card_id}/start', response=CardOut)
def start(request, card_id: int):
    card = visible_card(request, card_id)
    require_card_edit(request.user, card)
    return start_card(card, user=request.user)


@router.get('/cards/{card_id}/history', response=list[CardMoveOut])
def history(request, card_id: int):
    card = visible_card(request, card_id)
    return card.moves.select_related('user')


@router.get('/cards/{card_id}', response=CardOut)
def get_card(request, card_id: int):
    return visible_card(request, card_id, card_queryset())


@router.put('/cards/{card_id}', response={200: CardOut, 400: DetailOut})
def update_card(request, card_id: int, data: CardIn):
    card = visible_card(request, card_id)
    require_card_edit(request.user, card)
    before = {'assignee_id': card.assignee_id, 'due_date': card.due_date}
    changes = {}
    if data.fields is not None:
        try:
            card.custom_values, changes = merge_custom_values(card.project_id, card.custom_values, data.fields)
        except ValidationError as error:
            return Status(400, {'detail': ' '.join(error.messages)})
    card.title, card.description, card.due_date = data.title, data.description, data.due_date
    card.estimate_hours = data.estimate_hours
    card.assignee = resolve_assignee(data.assignee_id)
    if data.sprint_id is not None:
        sprint = project_sprint_or_400(card.project_id, data.sprint_id)
        if isinstance(sprint, Status):
            return sprint
        card.sprint = sprint
    card.save(
        update_fields=[
            'title',
            'description',
            'due_date',
            'estimate_hours',
            'assignee',
            'sprint',
            'custom_values',
            'modified',
        ]
    )
    record_card_changes(card, request.user, before)
    if changes:
        record(card, 'fields', request.user, changes=changes)
    sync_issue_fields(card)
    broadcast.card_updated(card, request.user)
    return card


@router.delete('/cards/{card_id}', response={204: None})
def remove_card(request, card_id: int):
    card = visible_card(request, card_id)
    require_card_delete(request.user, card)
    delete_card(card, user=request.user)
    return Status(204, None)


@router.post('/cards/{card_id}/archive', response=CardOut)
def archive(request, card_id: int):
    card = visible_card(request, card_id)
    require_card_delete(request.user, card)
    return move_card(card, Column.ARCHIVED, user=request.user)


@router.get('/cards/{card_id}/comments', response=list[CommentOut])
def list_comments(request, card_id: int):
    card = visible_card(request, card_id)
    return card.comments.select_related('author').prefetch_related('mentions')


@router.post('/cards/{card_id}/comments', response={201: CommentOut})
def add_comment(request, card_id: int, data: CommentIn):
    card = visible_card(request, card_id, Card.objects.select_related('project__client'))
    comment = Comment.objects.create(card=card, author=request.user, text=data.text)
    notify_mentions(comment)
    return Status(201, comment)


def own_comment_or_403(request, comment_id, allow_perm=None):
    comment = get_object_or_404(Comment.objects.select_related('author'), id=comment_id)
    if comment.author_id != request.user.id and not (allow_perm and has_perm(request.user, allow_perm)):
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
    own_comment_or_403(request, comment_id, allow_perm='boards.delete_comment').delete()
    return Status(204, None)


def label_name_taken(project_id, name, exclude_id=None):
    return Label.objects.filter(project_id=project_id, name__iexact=name).exclude(id=exclude_id).exists()


@router.get('/projects/{project_id}/labels', response=list[LabelOut])
def list_labels(request, project_id: int):
    return visible_project_or_404(request.user, project_id).labels.all()


@router.post('/projects/{project_id}/labels', response={201: LabelOut, 400: DetailOut})
def add_label(request, project_id: int, data: LabelIn):
    require(request.user, 'boards.add_label')
    project = visible_project_or_404(request.user, project_id)
    if label_name_taken(project.id, data.name):
        return Status(400, {'detail': 'Já existe uma etiqueta com este nome no projeto.'})
    return Status(201, Label.objects.create(project=project, **data.dict()))


@router.put('/labels/{label_id}', response={200: LabelOut, 400: DetailOut})
def update_label(request, label_id: int, data: LabelIn):
    label = visible_in_project_or_404(request.user, Label.objects, id=label_id)
    require(request.user, 'boards.change_label')
    if label_name_taken(label.project_id, data.name, exclude_id=label.id):
        return Status(400, {'detail': 'Já existe uma etiqueta com este nome no projeto.'})
    label.name, label.color = data.name, data.color
    label.save()
    return label


@router.delete('/labels/{label_id}', response={204: None})
def delete_label(request, label_id: int):
    label = visible_in_project_or_404(request.user, Label.objects, id=label_id)
    require(request.user, 'boards.delete_label')
    label.delete()
    return Status(204, None)


@router.put('/cards/{card_id}/labels', response={200: CardOut, 400: DetailOut})
def set_card_labels(request, card_id: int, data: CardLabelsIn):
    card = visible_card(request, card_id)
    require_card_edit(request.user, card)
    labels = Label.objects.filter(id__in=data.label_ids)
    if labels.exclude(project_id=card.project_id).exists() or labels.count() != len(set(data.label_ids)):
        return Status(400, {'detail': 'Use só etiquetas deste projeto.'})
    card.labels.set(labels)
    record_labels(card, request.user)
    broadcast.card_updated(card, request.user)
    return card


@router.get('/cards/{card_id}/checklist', response=list[ChecklistItemOut])
def list_checklist(request, card_id: int):
    return get_object_or_404(Card, id=card_id).checklist_items.all()


@router.post('/cards/{card_id}/checklist', response={201: ChecklistItemOut})
def add_checklist_item(request, card_id: int, data: ChecklistItemIn):
    card = get_object_or_404(Card, id=card_id)
    position = card.checklist_items.count()
    item = ChecklistItem.objects.create(card=card, position=position, **data.dict())
    broadcast.card_updated(card, request.user)
    return Status(201, item)


@router.put('/checklist/{item_id}', response=ChecklistItemOut)
def update_checklist_item(request, item_id: int, data: ChecklistItemIn):
    item = get_object_or_404(ChecklistItem, id=item_id)
    item.text, item.done = data.text, data.done
    item.save(update_fields=['text', 'done'])
    broadcast.card_updated(item.card, request.user)
    return item


@router.delete('/checklist/{item_id}', response={204: None})
def delete_checklist_item(request, item_id: int):
    item = get_object_or_404(ChecklistItem, id=item_id)
    card = item.card
    item.delete()
    renumber(list(ChecklistItem.objects.filter(card_id=card.id)))
    broadcast.card_updated(card, request.user)
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
    return visible_card(request, card_id).attachments.select_related('uploaded_by')


@router.post('/cards/{card_id}/attachments', response={201: AttachmentOut, 400: DetailOut})
def add_attachment(request, card_id: int, file: UploadedFile = File(...)):
    card = visible_card(request, card_id)
    require_card_edit(request.user, card)  # anexo segue a regra do card
    limit = settings.ATTACHMENT_MAX_BYTES
    if file.size > limit:
        return Status(400, {'detail': f'Arquivo grande demais. O tamanho máximo é {limit / 1024 / 1024:.0f} MB.'})
    attachment = Attachment(card=card, name=file.name, size=file.size, uploaded_by=request.user)
    attachment.file.save(file.name, file, save=True)
    broadcast.card_updated(card, request.user)
    return Status(201, attachment)


@router.delete('/attachments/{attachment_id}', response={204: None})
def delete_attachment(request, attachment_id: int):
    attachment = get_object_or_404(
        Attachment.objects.select_related('card').filter(card__project__in=visible_projects(request.user)),
        id=attachment_id,
    )
    card = attachment.card
    if attachment.uploaded_by_id != request.user.id:
        require_card_edit(request.user, card)  # quem enviou, ou quem pode editar o card
    attachment.file.delete(save=False)
    attachment.delete()
    broadcast.card_updated(card, request.user)
    return Status(204, None)


@router.get('/cards/{card_id}/activity', response=list[ActivityOut])
def activity(request, card_id: int):
    return card_activity(get_object_or_404(Card, id=card_id))


def notifications_payload(user):
    """Não lidas primeiro, depois as mais recentes (até 50), e o total de não lidas para o sino."""
    notes = Notification.objects.filter(user=user).select_related('actor', 'card')
    items = notes.order_by(F('read_at').asc(nulls_first=True), '-created', '-id')[:50]
    return {'unread': notes.filter(read_at__isnull=True).count(), 'items': list(items)}


@router.get('/notifications', response=NotificationsOut)
def list_notifications(request):
    return notifications_payload(request.user)


@router.post('/notifications/read-all', response=NotificationsOut)
def read_all_notifications(request):
    Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return notifications_payload(request.user)


@router.post('/notifications/{notification_id}/read', response=NotificationsOut)
def read_notification(request, notification_id: int):
    note = get_object_or_404(Notification, id=notification_id, user=request.user)
    if note.read_at is None:
        note.read_at = timezone.now()
        note.save(update_fields=['read_at', 'modified'])
    return notifications_payload(request.user)


@router.get('/me/cards', response=list[DashboardCardOut])
def my_cards(request):
    """Cards em aberto sob a responsabilidade de quem está logado: vencidos primeiro, depois por prazo."""
    today = timezone.localdate()
    overdue = Case(When(due_date__lt=today, then=Value(0)), default=Value(1))
    return (
        card_queryset()
        .filter(assignee=request.user, project__in=visible_projects(request.user))
        .exclude(column__in=[Column.DONE, Column.ARCHIVED])
        .select_related('project__client', 'sprint')
        .order_by(overdue, F('due_date').asc(nulls_last=True), 'project__name', 'number')
    )


def project_fields(project_id):
    return CustomField.objects.filter(project_id=project_id)


def save_field(field, data):
    """Aplica os dados, valida tipo/opções e nome único no projeto; devolve 400 quando algo não serve."""
    field.name, field.kind, field.required = data.name.strip(), data.kind, data.required
    field.options = [o.strip() for o in data.options if o.strip()]
    if project_fields(field.project_id).filter(name__iexact=field.name).exclude(id=field.id).exists():
        return Status(400, {'detail': 'Já existe um campo com este nome no projeto.'})
    try:
        field.full_clean(exclude=['project', 'uuid'])
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    field.save()
    return None


@router.get('/projects/{project_id}/fields', response=list[CustomFieldOut])
def list_fields(request, project_id: int):
    return visible_project_or_404(request.user, project_id).custom_fields.all()


@router.post('/projects/{project_id}/fields', response={201: CustomFieldOut, 400: DetailOut})
def add_field(request, project_id: int, data: CustomFieldIn):
    project = visible_project_or_404(request.user, project_id)
    require(request.user, 'projects.change_project')
    field = CustomField(project=project)
    return save_field(field, data) or Status(201, field)


@router.put('/projects/{project_id}/fields/order', response=list[CustomFieldOut])
def order_fields(request, project_id: int, data: OrderIn):
    project = visible_project_or_404(request.user, project_id)
    require(request.user, 'projects.change_project')
    fields = {f.id: f for f in project.custom_fields.all()}
    ordered = [fields[i] for i in data.ids if i in fields] + [f for i, f in fields.items() if i not in data.ids]
    for position, field in enumerate(ordered):
        field.position = position
    CustomField.objects.bulk_update(ordered, ['position'])
    return ordered


def editable_field(request, field_id):
    field = visible_in_project_or_404(request.user, CustomField.objects, id=field_id)
    require(request.user, 'projects.change_project')
    return field


@router.put('/fields/{field_id}', response={200: CustomFieldOut, 400: DetailOut})
def update_field(request, field_id: int, data: CustomFieldIn):
    field = editable_field(request, field_id)
    return save_field(field, data) or field


@router.delete('/fields/{field_id}', response={204: None})
def delete_field(request, field_id: int):
    editable_field(request, field_id).delete()
    return Status(204, None)
