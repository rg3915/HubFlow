from typing import Literal

from ninja import Schema
from pydantic import field_validator

from hubflow.clients.schemas import emails_validos


class ProjectIn(Schema):
    client_id: int
    name: str
    provider: Literal['github', 'gitlab']
    owner: str
    repo: str
    description: str = ''
    emails: list[str] = []
    is_active: bool = True
    notify_on_created: bool = True
    notify_on_moved: bool = True
    notify_on_done: bool = True

    _emails = field_validator('emails')(emails_validos)


class ProjectOut(Schema):
    id: int
    client_id: int
    client_name: str
    name: str
    provider: str
    owner: str
    repo: str
    repository_url: str
    description: str
    emails: list[str]
    is_active: bool
    notify_on_created: bool
    notify_on_moved: bool
    notify_on_done: bool

    @staticmethod
    def resolve_client_name(obj):
        return obj.client.name
