from typing import Literal

from ninja import ModelSchema, Schema
from pydantic import field_validator

from hubflow.clients.schemas import ClientOut, emails_validos
from hubflow.sprints.models import Milestone, Sprint

from .models import Project


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


class ProjectOut(ModelSchema):
    client_id: int
    client_name: str
    repository_url: str
    emails: list[str]
    has_token: bool

    class Meta:
        model = Project
        fields = [
            'id', 'uuid', 'name', 'provider', 'owner', 'repo', 'description', 'emails', 'is_active',
            'notify_on_created', 'notify_on_moved', 'notify_on_done', 'gitlab_project_id', 'create_issues',
        ]  # fmt: skip

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


class SprintBriefOut(ModelSchema):
    class Meta:
        model = Sprint
        fields = ['id', 'number', 'name']


class MilestoneBriefOut(ModelSchema):
    class Meta:
        model = Milestone
        fields = ['id', 'title']


class ProjectFullOut(Schema):
    client: ClientOut
    project: ProjectOut
    sprint: SprintBriefOut
    milestone: MilestoneBriefOut | None
