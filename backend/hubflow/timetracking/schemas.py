from datetime import date, datetime

from ninja import Schema
from pydantic import field_validator

from hubflow.accounts.schemas import UserOut


class TimeEntryOut(Schema):
    id: int
    card_id: int
    user: UserOut
    started_at: datetime
    ended_at: datetime | None
    note: str
    is_manual: bool
    is_running: bool
    hours: float


class CardTimeOut(Schema):
    entries: list[TimeEntryOut]
    total_hours: float
    running: TimeEntryOut | None


class ManualEntryIn(Schema):
    hours: float
    date: date
    note: str = ''

    @field_validator('hours')
    @classmethod
    def horas_positivas(cls, value):
        if value <= 0:
            raise ValueError('As horas precisam ser maiores que zero.')
        return value
