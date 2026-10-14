from datetime import date

from ninja import ModelSchema, Schema
from pydantic import field_validator

from hubflow.accounts.schemas import UserOut

from .models import TimeEntry


class TimeEntryOut(ModelSchema):
    card_id: int
    user: UserOut
    is_running: bool
    hours: float

    class Meta:
        model = TimeEntry
        fields = ['id', 'uuid', 'started_at', 'ended_at', 'note', 'is_manual']


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
