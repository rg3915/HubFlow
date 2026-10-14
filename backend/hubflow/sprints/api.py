from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.projects.models import Project

from .models import Milestone
from .schemas import MilestoneIn, MilestoneOut

router = Router(tags=['sprints'])


@router.get('/projects/{project_id}/milestones', response=list[MilestoneOut])
def list_milestones(request, project_id: int):
    return get_object_or_404(Project, id=project_id).milestones.all()


@router.post('/projects/{project_id}/milestones', response={201: MilestoneOut, 400: DetailOut})
def add_milestone(request, project_id: int, data: MilestoneIn):
    project = get_object_or_404(Project, id=project_id)
    if data.external_number and project.milestones.filter(external_number=data.external_number).exists():
        return Status(400, {'detail': 'Já existe um milestone com este número no projeto.'})
    return Status(201, Milestone.objects.create(project=project, **data.dict()))


@router.post('/milestones/{milestone_id}/close', response=MilestoneOut)
def close_milestone(request, milestone_id: int):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    milestone.is_open = False
    milestone.save(update_fields=['is_open'])
    return milestone
