import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from ninja import Schema
from pydantic import field_validator


class PaymentIn(Schema):
    project_id: int
    sprint_id: int | None = None
    month: str | None = None  # 'AAAA-MM' preenche o período com o mês inteiro
    period_start: date | None = None
    period_end: date | None = None
    description: str = ''
    hourly_rate: Decimal
    estimated_hours: Decimal | None = None
    fixed_value: Decimal | None = None
    invoice_number: str = ''
    issue_date: date | None = None
    payment_date: date | None = None

    @field_validator('hourly_rate')
    @classmethod
    def valor_hora_positivo(cls, value):
        if value <= 0:
            raise ValueError('O valor por hora precisa ser maior que zero.')
        return value

    @field_validator('month')
    @classmethod
    def mes_valido(cls, value):
        if value is None:
            return None
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', value):
            raise ValueError('Use o formato AAAA-MM, por exemplo 2026-10.')
        return value


class PaymentOut(Schema):
    id: int
    sprint_id: int | None
    sprint_number: int | None
    period_start: date | None
    period_end: date | None
    scope: str
    project_id: int
    project_name: str
    client_id: int
    client_name: str
    description: str
    hourly_rate: Decimal
    estimated_hours: Decimal | None
    estimated_value: Decimal | None
    spent_hours: Decimal
    fixed_value: Decimal | None
    total_value: Decimal
    invoice_number: str
    issue_date: date | None
    payment_date: date | None
    status: Literal['pending', 'paid']
    created: datetime

    @staticmethod
    def resolve_sprint_number(payment):
        return payment.sprint.number if payment.sprint_id else None

    @staticmethod
    def resolve_project_name(payment):
        return payment.project.name

    @staticmethod
    def resolve_client_id(payment):
        return payment.project.client_id

    @staticmethod
    def resolve_client_name(payment):
        return payment.project.client.name


class ClientTotalsOut(Schema):
    client_id: int
    client_name: str
    received: Decimal
    pending: Decimal


class MonthTotalsOut(Schema):
    month: str
    received: Decimal
    pending: Decimal


class SummaryOut(Schema):
    received: Decimal
    pending: Decimal
    by_client: list[ClientTotalsOut]
    by_month: list[MonthTotalsOut]
    years: list[int]
