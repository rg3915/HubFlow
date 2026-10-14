from typing import Literal
from uuid import UUID

from ninja import Schema
from pydantic import field_validator

from hubflow.clients.schemas import ClientOut, emails_validos


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
    uuid: UUID
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
    has_token: bool
    gitlab_project_id: int | None
    create_issues: bool

    @staticmethod
    def resolve_client_name(obj):
        return obj.client.name

    @staticmethod
    def resolve_has_token(obj):
        return bool(obj.repo_token)


class ProjectFullIn(Schema):
    client_name: str
    client_emails: list[str] = []
    name: str
    provider: Literal['github', 'gitlab']
    owner: str
    repo: str
    description: str = ''
    emails: list[str] = []
    milestone_title: str = ''

    _emails = field_validator('emails', 'client_emails')(emails_validos)


class SprintBriefOut(Schema):
    id: int
    number: int
    name: str


class MilestoneBriefOut(Schema):
    id: int
    title: str


class ProjectFullOut(Schema):
    client: ClientOut
    project: ProjectOut
    sprint: SprintBriefOut
    milestone: MilestoneBriefOut | None
