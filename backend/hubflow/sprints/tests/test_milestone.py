import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Milestone, Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def test_titulo_obrigatorio(loja):
    with pytest.raises(ValidationError):
        Milestone(project=loja, title='').full_clean()


def test_numero_externo_unico_por_projeto_mas_opcional(loja):
    Milestone.objects.create(project=loja, title='v1', external_number=1)
    Milestone.objects.create(project=loja, title='sem número')
    Milestone.objects.create(project=loja, title='outra sem número')

    with pytest.raises(IntegrityError):
        Milestone.objects.create(project=loja, title='repetido', external_number=1)


def test_sprint_pode_apontar_para_milestone(loja):
    milestone = Milestone.objects.create(project=loja, title='v1')

    sprint = Sprint.objects.create(project=loja, milestone=milestone)

    assert sprint.milestone == milestone
    assert list(milestone.sprints.all()) == [sprint]


def test_excluir_milestone_mantem_a_sprint(loja):
    milestone = Milestone.objects.create(project=loja, title='v1')
    sprint = Sprint.objects.create(project=loja, milestone=milestone)

    milestone.delete()

    sprint.refresh_from_db()
    assert sprint.milestone is None


def test_api_lista_e_cria_milestones(api, loja):
    response = api.post(f'/api/projects/{loja.id}/milestones', {'title': 'v1', 'external_number': 1}, **JSON)

    assert response.status_code == 201
    assert response.json()['title'] == 'v1'
    listed = api.get(f'/api/projects/{loja.id}/milestones').json()
    assert [m['title'] for m in listed] == ['v1']


def test_api_numero_externo_repetido_retorna_400(api, loja):
    api.post(f'/api/projects/{loja.id}/milestones', {'title': 'v1', 'external_number': 1}, **JSON)

    response = api.post(f'/api/projects/{loja.id}/milestones', {'title': 'v2', 'external_number': 1}, **JSON)

    assert response.status_code == 400


def test_api_fecha_milestone(api, loja):
    milestone_id = api.post(f'/api/projects/{loja.id}/milestones', {'title': 'v1'}, **JSON).json()['id']

    response = api.post(f'/api/milestones/{milestone_id}/close')

    assert response.status_code == 200
    assert Milestone.objects.get(id=milestone_id).is_open is False
