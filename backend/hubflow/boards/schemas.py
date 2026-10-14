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
