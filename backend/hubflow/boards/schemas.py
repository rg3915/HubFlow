from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import field_validator


class CardIn(Schema):
    title: str
    description: str = ''

    @field_validator('title')
    @classmethod
    def titulo_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O título é obrigatório.')  # RN-38
        return value.strip()


class CardOut(Schema):
    id: int
    project_id: int
    number: int
    title: str
    description: str
    column: str
    position: int


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
