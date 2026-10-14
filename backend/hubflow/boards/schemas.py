import re
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from ninja import Field, Schema
from pydantic import field_validator

from hubflow.accounts.schemas import UserOut


class CardIn(Schema):
    title: str
    description: str = ''
    due_date: date | None = None
    assignee_id: int | None = None
    sprint_id: int | None = None
    estimate_hours: float | None = None
    fields: dict[str, Any] | None = None  # campos personalizados {id: valor}; omitido = não mexe

    @field_validator('estimate_hours')
    @classmethod
    def estimativa_nao_negativa(cls, value):
        if value is not None and value < 0:
            raise ValueError('A estimativa não pode ser negativa.')
        return value

    @field_validator('title')
    @classmethod
    def titulo_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O título é obrigatório.')  # RN-38
        return value.strip()


class LabelIn(Schema):
    name: str
    color: str

    @field_validator('name')
    @classmethod
    def nome_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O nome é obrigatório.')
        return value.strip()

    @field_validator('color')
    @classmethod
    def cor_hex(cls, value):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            raise ValueError('Use uma cor no formato #rrggbb.')
        return value.lower()


class LabelOut(Schema):
    id: int
    uuid: UUID
    project_id: int
    name: str
    color: str


class CardLabelsIn(Schema):
    label_ids: list[int]


class ChecklistItemIn(Schema):
    text: str
    done: bool = False

    @field_validator('text')
    @classmethod
    def texto_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O texto é obrigatório.')
        return value.strip()


class ChecklistItemOut(Schema):
    id: int
    uuid: UUID
    card_id: int
    text: str
    done: bool
    position: int


class ChecklistOrderIn(Schema):
    item_ids: list[int]


class ChecklistSummary(Schema):
    done: int
    total: int


class AttachmentOut(Schema):
    id: int
    uuid: UUID
    card_id: int
    name: str
    size: int
    url: str
    uploaded_by: UserOut
    created: datetime

    @staticmethod
    def resolve_url(attachment):
        return attachment.file.url


class SprintBrief(Schema):
    id: int
    number: int
    name: str


class TimeSummary(Schema):
    hours: float
    running: bool


class ProgressOut(Schema):
    spent_hours: float
    estimate_hours: float | None
    percent: int | None
    source: str | None


class CardOut(Schema):
    id: int
    uuid: UUID
    project_id: int
    number: int
    title: str
    description: str
    column: str
    position: int
    labels: list[LabelOut]
    due_date: date | None
    assignee: UserOut | None
    created_by: UserOut | None
    is_overdue: bool
    checklist: ChecklistSummary
    attachments_count: int
    sprint: SprintBrief | None
    custom_values: dict[str, Any]
    estimate_hours: float | None
    issue_number: int | None
    issue_url: str
    time: TimeSummary
    progress: ProgressOut

    @staticmethod
    def spent_hours(card):
        if hasattr(card, 'time_spent'):
            return round(card.time_spent.total_seconds() / 3600, 2) if card.time_spent else 0.0
        from hubflow.timetracking.models import TimeEntry

        return round(TimeEntry.objects.total_for(card).total_seconds() / 3600, 2)

    @staticmethod
    def resolve_time(card):
        if hasattr(card, 'time_running'):
            running = card.time_running
        else:
            from hubflow.timetracking.models import TimeEntry

            running = TimeEntry.objects.running_for(card) is not None
        return {'hours': CardOut.spent_hours(card), 'running': running}

    @staticmethod
    def resolve_progress(card):
        from hubflow.timetracking.services import card_progress, project_median_estimate

        # O quadro calcula a mediana uma vez por projeto e anota em cada card; fora dele, calcula aqui.
        median = card.project_median if hasattr(card, 'project_median') else project_median_estimate(card.project_id)
        return card_progress(card, CardOut.spent_hours(card), median)

    @staticmethod
    def resolve_attachments_count(card):
        return card.attachments_count if hasattr(card, 'attachments_count') else card.attachments.count()

    @staticmethod
    def resolve_checklist(card):
        # Vem das anotações de card_queryset(); fora delas, conta no banco (um card só).
        if hasattr(card, 'checklist_total'):
            return {'done': card.checklist_done, 'total': card.checklist_total}
        items = list(card.checklist_items.values_list('done', flat=True))
        return {'done': sum(items), 'total': len(items)}


class ColumnOut(Schema):
    key: str
    label: str
    cards: list[CardOut]


class BoardProjectOut(Schema):
    id: int
    name: str
    client_name: str


class BoardOut(Schema):
    project: BoardProjectOut
    columns: list[ColumnOut]


class MoveIn(Schema):
    column: Literal['backlog', 'sprint', 'doing', 'qa', 'done', 'archived']
    position: int | None = None


class CardMoveOut(Schema):
    from_column: str
    to_column: str
    user_email: str | None
    created: datetime

    @staticmethod
    def resolve_user_email(obj):
        return obj.user.email if obj.user else None


class CommentIn(Schema):
    text: str

    @field_validator('text')
    @classmethod
    def texto_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O comentário não pode ficar vazio.')
        return value.strip()


class CommentOut(Schema):
    id: int
    uuid: UUID
    card_id: int
    author: UserOut
    text: str
    mentions: list[UserOut]
    created: datetime
    modified: datetime


class ActivityOut(Schema):
    kind: str
    user: UserOut | None
    data: dict
    created: datetime


class NotificationOut(Schema):
    id: int
    uuid: UUID
    kind: str
    text: str
    read: bool
    created: datetime
    actor_name: str | None
    card_id: int
    card_number: int
    card_title: str
    project_id: int

    @staticmethod
    def resolve_read(obj):
        return obj.read_at is not None

    @staticmethod
    def resolve_actor_name(obj):
        return (obj.actor.name or obj.actor.email) if obj.actor else None

    @staticmethod
    def resolve_card_number(obj):
        return obj.card.number

    @staticmethod
    def resolve_card_title(obj):
        return obj.card.title

    @staticmethod
    def resolve_project_id(obj):
        return obj.card.project_id


class NotificationsOut(Schema):
    unread: int
    items: list[NotificationOut]


class CustomFieldIn(Schema):
    name: str = Field(min_length=1, max_length=80)
    kind: str
    options: list[str] = []
    required: bool = False


class CustomFieldOut(Schema):
    id: int
    uuid: UUID
    project_id: int
    name: str
    kind: str
    options: list[str]
    required: bool
    position: int


class OrderIn(Schema):
    ids: list[int]
