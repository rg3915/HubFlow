import pytest
import respx
from httpx import Response

from hubflow.sprints.models import Milestone, Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
MILESTONES = 'https://api.github.com/repos/acme/loja/milestones'


@pytest.fixture
def github(loja):
    loja.repo_token = 'ghp_x'
    loja.save()
    return loja


@respx.mock
def test_sprint_nova_pega_o_ultimo_milestone_aberto_do_repositorio(api, github):
    respx.get(MILESTONES).mock(
        return_value=Response(
            200, json=[{'number': 3, 'title': 'v0.3'}, {'number': 5, 'title': 'v0.5'}, {'number': 4, 'title': 'v0.4'}]
        )
    )

    response = api.post(f'/api/projects/{github.id}/sprints', {}, **JSON)

    assert response.status_code == 201
    milestone = response.json()['milestone']
    assert (milestone['title'], milestone['external_number']) == ('v0.5', 5)
    assert Milestone.objects.filter(project=github, external_number=5).count() == 1


@respx.mock
def test_milestone_ja_conhecido_e_reaproveitado(api, github):
    existing = Milestone.objects.create(project=github, title='v0.5', external_number=5)
    respx.get(MILESTONES).mock(return_value=Response(200, json=[{'number': 5, 'title': 'v0.5'}]))

    data = api.post(f'/api/projects/{github.id}/sprints', {}, **JSON).json()

    assert data['milestone']['id'] == existing.id
    assert Milestone.objects.count() == 1


@respx.mock
def test_milestone_informado_nao_consulta_o_repositorio(api, github):
    mine = Milestone.objects.create(project=github, title='Manual')
    route = respx.get(MILESTONES)

    data = api.post(f'/api/projects/{github.id}/sprints', {'milestone_id': mine.id}, **JSON).json()

    assert not route.called and data['milestone']['id'] == mine.id


@respx.mock
def test_sem_milestone_aberto_a_sprint_fica_sem_milestone(api, github):
    respx.get(MILESTONES).mock(return_value=Response(200, json=[]))

    data = api.post(f'/api/projects/{github.id}/sprints', {}, **JSON).json()

    assert data['milestone'] is None


def test_projeto_sem_token_nao_consulta(api, loja):
    data = api.post(f'/api/projects/{loja.id}/sprints', {}, **JSON).json()

    assert data['milestone'] is None


@respx.mock
def test_falha_no_repositorio_nao_impede_a_sprint(api, github):
    respx.get(MILESTONES).mock(return_value=Response(500, json={}))

    response = api.post(f'/api/projects/{github.id}/sprints', {}, **JSON)

    assert response.status_code == 201 and response.json()['milestone'] is None


@respx.mock
def test_gitlab_usa_milestones_ativos(api, loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id = 'gitlab', 'glpat', 7
    loja.save()
    route = respx.get('https://gitlab.com/api/v4/projects/7/milestones').mock(
        return_value=Response(200, json=[{'id': 900, 'iid': 2, 'title': 'Sprint 2', 'state': 'active'}])
    )

    data = api.post(f'/api/projects/{loja.id}/sprints', {}, **JSON).json()

    assert route.calls.last.request.url.params['state'] == 'active'
    assert (data['milestone']['title'], data['milestone']['external_number']) == ('Sprint 2', 2)
    assert Sprint.objects.get(id=data['id']).milestone.external_number == 2
