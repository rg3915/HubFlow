from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.projects.models import Project

from . import presence
from .schemas import PresenceOut

router = Router(tags=['realtime'])


@router.get('/projects/{project_id}/presence', response=PresenceOut)
def who_is_viewing(request, project_id: int):
    get_object_or_404(Project, id=project_id)
    return {'viewers': presence.viewer_users(project_id)}


@router.post('/projects/{project_id}/presence', response=PresenceOut)
def heartbeat(request, project_id: int):
    """O quadro chama a cada poucos segundos; a presença expira sozinha sem heartbeat."""
    get_object_or_404(Project, id=project_id)
    presence.touch(project_id, request.user.id)
    return {'viewers': presence.announce(project_id)}


@router.delete('/projects/{project_id}/presence', response={204: None})
def leave_board(request, project_id: int):
    presence.leave(project_id, request.user.id)
    presence.announce(project_id)
    return Status(204, None)
