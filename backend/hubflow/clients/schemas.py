from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import field_validator


def emails_validos(cls, value):
    for email in value:
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(f'E-mail inválido: {email}')
    return value


class ClientIn(Schema):
    name: str
    emails: list[str] = []
    is_active: bool = True

    _emails = field_validator('emails')(emails_validos)


class ClientOut(Schema):
    id: int
    uuid: UUID
    name: str
    emails: list[str]
    is_active: bool
