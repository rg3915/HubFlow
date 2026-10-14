from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja import Schema
from pydantic import field_validator


class ClientIn(Schema):
    name: str
    emails: list[str] = []
    is_active: bool = True

    @field_validator('emails')
    @classmethod
    def emails_validos(cls, value):
        for email in value:
            try:
                validate_email(email)
            except ValidationError:
                raise ValueError(f'E-mail inválido: {email}')
        return value


class ClientOut(Schema):
    id: int
    name: str
    emails: list[str]
    is_active: bool
