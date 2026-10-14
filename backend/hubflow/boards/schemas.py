import re
from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import field_validator

from hubflow.accounts.schemas import UserOut


class CardIn(Schema):
    title: str
    description: str = ''

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


class CardOut(Schema):
    id: int
    project_id: int
    number: int
    title: str
    description: str
    column: str
    position: int
    labels: list[LabelOut]


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
