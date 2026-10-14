import re
from datetime import date, datetime
from typing import Literal

from ninja import Schema
from pydantic import field_validator

from hubflow.accounts.schemas import UserOut


class CardIn(Schema):
    title: str
    description: str = ''
    due_date: date | None = None
    assignee_id: int | None = None
    sprint_id: int | None = None

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


class CardOut(Schema):
    id: int
    project_id: int
    number: int
    title: str
    description: str
    column: str
    position: int
    labels: list[LabelOut]
    due_date: date | None
    assignee: UserOut | None
    is_overdue: bool
    checklist: ChecklistSummary
    attachments_count: int
    sprint: SprintBrief | None
    time: TimeSummary

    @staticmethod
    def resolve_time(card):
        if hasattr(card, 'time_spent'):
            spent = card.time_spent.total_seconds() / 3600 if card.time_spent else 0.0
            return {'hours': round(spent, 2), 'running': card.time_running}
        from hubflow.timetracking.models import TimeEntry

        total = TimeEntry.objects.total_for(card).total_seconds() / 3600
        return {'hours': round(total, 2), 'running': TimeEntry.objects.running_for(card) is not None}

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
