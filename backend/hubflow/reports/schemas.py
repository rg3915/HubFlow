from datetime import date
from decimal import Decimal

from ninja import Schema


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
