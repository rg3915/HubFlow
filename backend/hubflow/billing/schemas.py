from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from ninja import Schema
from pydantic import field_validator


class PaymentIn(Schema):
    sprint_id: int
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


class PaymentOut(Schema):
    id: int
    sprint_id: int
    sprint_number: int
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
        return payment.sprint.number

    @staticmethod
    def resolve_project_id(payment):
        return payment.sprint.project_id

    @staticmethod
    def resolve_project_name(payment):
        return payment.sprint.project.name

    @staticmethod
    def resolve_client_id(payment):
        return payment.sprint.project.client_id

    @staticmethod
    def resolve_client_name(payment):
        return payment.sprint.project.client.name
