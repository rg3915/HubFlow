"""Formulário público do projeto: link com token que cria card no Backlog sem login (RN-101)."""

import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from hubflow.accounts.schemas import DetailOut
from hubflow.permissions.services import require, visible_project_or_404
from hubflow.projects.models import Project

from .schemas import CustomFieldOut
from .services import create_card, merge_custom_values

router = Router(tags=['forms'])


class FormSettingsIn(Schema):
    enabled: bool


class FormSettingsOut(Schema):
    enabled: bool
    token: str
    path: str


class PublicFormOut(Schema):
    project_name: str
    client_name: str
    fields: list[CustomFieldOut]


class SubmissionIn(Schema):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field('', max_length=5000)
    email: str = Field('', max_length=254)  # contato de quem enviou (opcional)
    fields: dict = {}


class SubmissionOut(Schema):
    number: int


def form_settings(project):
    return {'enabled': project.form_enabled, 'token': project.form_token, 'path': f'/form/{project.form_token}'}


def managed_project(request, project_id):
    project = visible_project_or_404(request.user, project_id)
    require(request.user, 'projects.change_project')
    return project


@router.get('/projects/{project_id}/form', response=FormSettingsOut)
def get_form(request, project_id: int):
    return form_settings(managed_project(request, project_id))


@router.put('/projects/{project_id}/form', response=FormSettingsOut)
def set_form(request, project_id: int, data: FormSettingsIn):
    project = managed_project(request, project_id)
    project.form_enabled = data.enabled
    project.form_token = project.form_token or secrets.token_urlsafe(24)
    project.save(update_fields=['form_enabled', 'form_token', 'modified'])
    return form_settings(project)


@router.post('/projects/{project_id}/form/regenerate', response=FormSettingsOut)
def regenerate_form(request, project_id: int):
    """Novo link: o anterior para de funcionar."""
    project = managed_project(request, project_id)
    project.form_token = secrets.token_urlsafe(24)
    project.save(update_fields=['form_token', 'modified'])
    return form_settings(project)


def open_form(token):
    return get_object_or_404(
        Project.objects.select_related('client'), form_token=token, form_enabled=True, is_active=True
    )


@router.get('/forms/{token}', response=PublicFormOut, auth=None)
def public_form(request, token: str):
    project = open_form(token)
    return {'project_name': project.name, 'client_name': project.client.name, 'fields': project.custom_fields.all()}


def check_rate(request):
    # ponytail: contador no cache padrão (memória local, por processo); com vários processos, usar Redis no CACHES.
    key = f'form-submissions:{request.META.get("REMOTE_ADDR", "")}'
    cache.add(key, 0, timeout=3600)
    if cache.incr(key) > settings.FORM_SUBMISSIONS_PER_HOUR:
        raise HttpError(429, 'Muitos envios a partir deste endereço. Tente de novo mais tarde.')


@router.post('/forms/{token}', response={201: SubmissionOut, 400: DetailOut}, auth=None)
def submit_form(request, token: str, data: SubmissionIn):
    project = open_form(token)
    check_rate(request)
    try:
        values, _ = merge_custom_values(project, {}, data.fields, creating=True)
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    sender = f' por {data.email}' if data.email else ''
    description = f'{data.description.strip()}\n\nEnviado pelo formulário público{sender}.'.strip()
    card = create_card(project, title=data.title, description=description, custom_values=values)
    return Status(201, {'number': card.number})
