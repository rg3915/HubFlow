from datetime import date, datetime

from ninja import Schema
from pydantic import field_validator


class MilestoneIn(Schema):
    title: str
    external_number: int | None = None

    @field_validator('title')
    @classmethod
    def titulo_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O título é obrigatório.')
        return value.strip()


class MilestoneOut(Schema):
    id: int
    project_id: int
    title: str
    external_number: int | None
    is_open: bool


class SprintIn(Schema):
    name: str = ''
    milestone_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintOut(Schema):
    id: int
    project_id: int
    number: int
    name: str
    milestone: MilestoneOut | None
    start_date: date | None
    end_date: date | None
    is_open: bool
    closed_at: datetime | None
