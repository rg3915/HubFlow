import pytest

from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Milestone, Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def payload(**overrides):
    return {'client_name': 'ACME', 'name': 'Loja', 'provider': 'github', 'owner': 'acme', 'repo': 'loja'} | overrides


def test_cria_cliente_projeto_e_sprint_1(api):
    response = api.post('/api/projects/full', payload(), **JSON)

    assert response.status_code == 201
    data = response.json()
    project = Project.objects.get(id=data['project']['id'])
    assert project.client.name == 'ACME'
    assert data['sprint']['number'] == 1
    assert data['milestone'] is None
    assert Sprint.objects.get(project=project).number == 1


def test_reaproveita_cliente_existente_sem_diferenciar_maiusculas(api):
    acme = Client.objects.create(name='ACME')

    response = api.post('/api/projects/full', payload(client_name='acme'), **JSON)

    assert response.status_code == 201
    assert response.json()['client']['id'] == acme.id
    assert Client.objects.count() == 1


def test_milestone_opcional(api):
    response = api.post('/api/projects/full', payload(milestone_title='v1.0'), **JSON)

    data = response.json()
    assert data['milestone']['title'] == 'v1.0'
    assert Sprint.objects.get(id=data['sprint']['id']).milestone == Milestone.objects.get(id=data['milestone']['id'])


def test_conflito_de_repositorio_nao_cria_nada(api):
    acme = Client.objects.create(name='ACME')
    Project.objects.create(client=acme, name='Antigo', provider='github', owner='acme', repo='loja')

    response = api.post('/api/projects/full', payload(client_name='Beta'), **JSON)

    assert response.status_code == 400
    assert not Client.objects.filter(name='Beta').exists()
    assert Project.objects.count() == 1


def test_cliente_novo_recebe_emails(api):
    response = api.post('/api/projects/full', payload(client_emails=['ti@hubflow.com']), **JSON)

    assert Client.objects.get(id=response.json()['client']['id']).emails == ['ti@hubflow.com']
