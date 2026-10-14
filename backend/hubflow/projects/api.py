from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.boards.services import archive_project
from hubflow.clients.models import Client
from hubflow.permissions.services import require, visible_clients, visible_projects
from hubflow.sprints.models import Milestone, Sprint

from .models import Project
from .schemas import ProjectFullIn, ProjectFullOut, ProjectIn, ProjectOut

router = Router(tags=['projects'])


def conflict(data, exclude_id=None):
    """Devolve a mensagem de conflito (RN-21, RN-22) ou None."""
    others = Project.objects.exclude(id=exclude_id)
    if others.filter(client_id=data.client_id, name=data.name).exists():
        return 'Já existe um projeto com este nome neste cliente.'
    if others.filter(provider=data.provider, owner=data.owner, repo=data.repo).exists():
        return 'Este repositório já está ligado a outro projeto.'
    return None


@router.get('', response=list[ProjectOut])
def list_projects(request, client: int | None = None):
    projects = visible_projects(request.user)
    if client is not None:
        projects = projects.filter(client_id=client)
    return projects


@router.post('', response={201: ProjectOut, 400: DetailOut})
def create_project(request, data: ProjectIn):
    require(request.user, 'projects.add_project')
    get_object_or_404(visible_clients(request.user), id=data.client_id)
    if message := conflict(data):
        return Status(400, {'detail': message})
    return Status(201, Project.objects.create(**data.dict()))


@router.post('/full', response={201: ProjectFullOut, 400: DetailOut})
def create_project_full(request, data: ProjectFullIn):
    """Cliente (se não existir) + projeto + sprint 1 (+ milestone opcional) numa transação só."""
    require(request.user, 'projects.add_project')
    with transaction.atomic():
        client = Client.objects.filter(name__iexact=data.client_name).first()
        if client is None:
            client = Client.objects.create(name=data.client_name, emails=data.client_emails)
        project_data = ProjectIn(
            client_id=client.id,
            name=data.name,
            provider=data.provider,
            owner=data.owner,
            repo=data.repo,
            description=data.description,
            emails=data.emails,
        )
        if message := conflict(project_data):
            transaction.set_rollback(True)
            return Status(400, {'detail': message})
        project = Project.objects.create(**project_data.dict())
        milestone = (
            Milestone.objects.create(project=project, title=data.milestone_title) if data.milestone_title else None
        )
        sprint = Sprint.objects.create(project=project, milestone=milestone)
    return Status(201, {'client': client, 'project': project, 'sprint': sprint, 'milestone': milestone})


@router.get('/{project_id}', response=ProjectOut)
def get_project(request, project_id: int):
    return get_object_or_404(visible_projects(request.user), id=project_id)


@router.put('/{project_id}', response={200: ProjectOut, 400: DetailOut})
def update_project(request, project_id: int, data: ProjectIn):
    require(request.user, 'projects.change_project')
    project = get_object_or_404(visible_projects(request.user), id=project_id)
    get_object_or_404(visible_clients(request.user), id=data.client_id)
    if message := conflict(data, exclude_id=project.id):
        return Status(400, {'detail': message})
    for field, value in data.dict().items():
        setattr(project, field, value)
    project.save()
    return project


@router.delete('/{project_id}', response={204: None})
def delete_project(request, project_id: int):
    # RN-24: arquiva os cards e desativa o projeto.
    require(request.user, 'projects.delete_project')
    archive_project(get_object_or_404(visible_projects(request.user), id=project_id), user=request.user)
    return Status(204, None)
