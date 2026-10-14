from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.boards.services import archive_project
from hubflow.clients.models import Client

from .models import Project
from .schemas import ProjectIn, ProjectOut

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
    projects = Project.objects.select_related('client')
    if client is not None:
        projects = projects.filter(client_id=client)
    return projects


@router.post('', response={201: ProjectOut, 400: DetailOut})
def create_project(request, data: ProjectIn):
    get_object_or_404(Client, id=data.client_id)
    if message := conflict(data):
        return Status(400, {'detail': message})
    return Status(201, Project.objects.create(**data.dict()))


@router.get('/{project_id}', response=ProjectOut)
def get_project(request, project_id: int):
    return get_object_or_404(Project.objects.select_related('client'), id=project_id)


@router.put('/{project_id}', response={200: ProjectOut, 400: DetailOut})
def update_project(request, project_id: int, data: ProjectIn):
    project = get_object_or_404(Project, id=project_id)
    get_object_or_404(Client, id=data.client_id)
    if message := conflict(data, exclude_id=project.id):
        return Status(400, {'detail': message})
    for field, value in data.dict().items():
        setattr(project, field, value)
    project.save()
    return project


@router.delete('/{project_id}', response={204: None})
def delete_project(request, project_id: int):
    # RN-24: arquiva os cards e desativa o projeto.
    archive_project(get_object_or_404(Project, id=project_id), user=request.user)
    return Status(204, None)
