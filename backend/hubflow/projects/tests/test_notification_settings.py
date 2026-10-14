import pytest

from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme():
    return Client.objects.create(name='ACME')


def test_eventos_ligados_por_padrao(acme):
    # RN-41
    project = Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    assert (project.notify_on_created, project.notify_on_moved, project.notify_on_done) == (True, True, True)


def test_api_expoe_e_altera_as_preferencias(api, acme):
    data = {
        'client_id': acme.id,
        'name': 'Loja',
        'provider': 'github',
        'owner': 'acme',
        'repo': 'loja',
        'notify_on_moved': False,
    }

    response = api.post('/api/projects', data, content_type='application/json')

    assert response.status_code == 201
    body = response.json()
    assert (body['notify_on_created'], body['notify_on_moved'], body['notify_on_done']) == (True, False, True)

    data['notify_on_done'] = False
    response = api.put(f'/api/projects/{body["id"]}', data, content_type='application/json')

    assert response.json()['notify_on_done'] is False
