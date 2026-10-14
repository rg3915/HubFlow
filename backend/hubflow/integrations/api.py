from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.projects.models import Project

from .client import RepoClient, RepoError
from .schemas import ImportIssuesIn, ImportIssuesOut, RepoCheckOut, RepoSettingsIn, RepoSettingsOut
from .services import import_issues

router = Router(tags=['integrations'])


@router.get('/projects/{project_id}/repo', response=RepoSettingsOut)
def repo_settings(request, project_id: int):
    return get_object_or_404(Project, id=project_id)


@router.put('/projects/{project_id}/repo', response=RepoSettingsOut)
def update_repo_settings(request, project_id: int, data: RepoSettingsIn):
    project = get_object_or_404(Project, id=project_id)
    if data.token is not None:
        project.repo_token = data.token
    project.gitlab_project_id = data.gitlab_project_id
    project.create_issues = data.create_issues
    project.save(update_fields=['repo_token', 'gitlab_project_id', 'create_issues', 'modified'])
    return project


@router.post('/projects/{project_id}/repo/check', response={200: RepoCheckOut, 400: DetailOut})
def repo_check(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    try:
        return RepoClient(project).check()
    except RepoError as error:
        return Status(400, {'detail': str(error)})


@router.post('/projects/{project_id}/import-issues', response={200: ImportIssuesOut, 400: DetailOut})
def import_repo_issues(request, project_id: int, data: ImportIssuesIn):
    project = get_object_or_404(Project, id=project_id)
    try:
        return import_issues(project, user=request.user, include_closed=data.include_closed)
    except RepoError as error:
        return Status(400, {'detail': str(error)})
