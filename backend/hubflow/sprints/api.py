from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.projects.models import Project

from .models import Milestone, Sprint
from .schemas import MilestoneIn, MilestoneOut, SprintIn, SprintOut

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


def apply_sprint_data(sprint, data):
    """Aplica nome, milestone e datas; devolve a resposta 400 quando algo não serve."""
    if data.milestone_id is not None:
        if not Milestone.objects.filter(id=data.milestone_id, project_id=sprint.project_id).exists():
            return Status(400, {'detail': 'Use um milestone deste projeto.'})
    sprint.name, sprint.milestone_id = data.name, data.milestone_id
    sprint.start_date, sprint.end_date = data.start_date, data.end_date
    try:
        sprint.clean()
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    return None


def sprint_queryset():
    return Sprint.objects.select_related('milestone').annotate(cards_count=Count('cards'))


@router.get('/projects/{project_id}/sprints', response=list[SprintOut])
def list_sprints(request, project_id: int):
    get_object_or_404(Project, id=project_id)
    return sprint_queryset().filter(project_id=project_id).order_by('-number')


@router.post('/projects/{project_id}/sprints', response={201: SprintOut, 400: DetailOut})
def add_sprint(request, project_id: int, data: SprintIn):
    sprint = Sprint(project=get_object_or_404(Project, id=project_id))
    if error := apply_sprint_data(sprint, data):
        return error
    sprint.save()
    return Status(201, sprint)


@router.get('/projects/{project_id}/sprints/current', response=SprintOut)
def current_sprint(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    current = Sprint.objects.latest_open(project)
    if current is None:
        raise Http404('Nenhuma sprint aberta.')
    return sprint_queryset().get(id=current.id)


@router.put('/sprints/{sprint_id}', response={200: SprintOut, 400: DetailOut})
def update_sprint(request, sprint_id: int, data: SprintIn):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    if error := apply_sprint_data(sprint, data):
        return error
    sprint.save()
    return sprint


@router.post('/sprints/{sprint_id}/close', response=SprintOut)
def close_sprint(request, sprint_id: int):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    sprint.close()  # RN-62
    return sprint


@router.delete('/sprints/{sprint_id}', response={204: None, 400: DetailOut})
def delete_sprint(request, sprint_id: int):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    if sprint.cards.exists():
        return Status(400, {'detail': 'A sprint tem cards. Feche-a em vez de excluir.'})
    sprint.delete()
    return Status(204, None)
