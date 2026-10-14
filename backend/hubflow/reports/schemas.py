import datetime as dt
from datetime import date
from decimal import Decimal

from ninja import ModelSchema, Schema

from .models import ReportSchedule


class PeriodOut(Schema):
    kind: str
    label: str
    start: date
    end: date


class ScopeOut(Schema):
    client: str | None
    project: str | None


class UserHoursOut(Schema):
    name: str
    hours: float


class CardHoursOut(Schema):
    project: str
    number: int
    title: str
    hours: float


class HoursOut(Schema):
    total: float
    by_user: list[UserHoursOut]
    by_card: list[CardHoursOut]


class CardsOut(Schema):
    created: int
    done: int
    avg_days_to_done: float | None


class BillingOut(Schema):
    received: Decimal
    pending: Decimal


class ReportOut(Schema):
    period: PeriodOut
    scope: ScopeOut
    hours: HoursOut
    cards: CardsOut
    sla_breached: int
    billing: BillingOut | None


class ReportSendIn(Schema):
    client: int | None = None
    project: int | None = None
    period: str | None = None
    date: dt.date | None = None  # o campo se chama date: o tipo vem do módulo para não ser sombreado
    start: dt.date | None = None
    end: dt.date | None = None
    emails: list[str] = []  # vazio = e-mails do projeto ou do cliente


class SentOut(Schema):
    sent_to: list[str]


class ScheduleIn(Schema):
    client: int | None = None
    project: int | None = None
    frequency: str
    emails: list[str] = []
    is_active: bool = True


class ScheduleOut(ModelSchema):
    client_id: int | None
    project_id: int | None
    scope: str
    emails: list[str]

    class Meta:
        model = ReportSchedule
        fields = ['id', 'uuid', 'frequency', 'emails', 'is_active', 'last_period_end']

    @staticmethod
    def resolve_scope(schedule):
        return schedule.scope_name
