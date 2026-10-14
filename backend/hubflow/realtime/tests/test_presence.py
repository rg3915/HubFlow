import pytest
from django.contrib.auth import get_user_model
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.realtime.presence import clear_presence, viewers

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def limpa(loja):
    clear_presence(loja.id)
    yield
    clear_presence(loja.id)


def test_heartbeat_registra_quem_esta_vendo(api, loja, user):
    response = api.post(f'/api/projects/{loja.id}/presence')

    assert response.status_code == 200
    assert [v['email'] for v in response.json()['viewers']] == ['ana@example.com']
    assert viewers(loja.id) == [user.id]


def test_lista_todos_os_que_estao_vendo(api, loja, user):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123', name='Bob')
    bob_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=bob).key}'})
    api.post(f'/api/projects/{loja.id}/presence')
    bob_api.post(f'/api/projects/{loja.id}/presence')

    data = api.get(f'/api/projects/{loja.id}/presence').json()

    assert sorted(v['email'] for v in data['viewers']) == ['ana@example.com', 'bob@hubflow.com']
    assert data['viewers'][0]['first_name']


def test_sair_remove_da_lista(api, loja):
    api.post(f'/api/projects/{loja.id}/presence')

    response = api.delete(f'/api/projects/{loja.id}/presence')

    assert response.status_code == 204
    assert viewers(loja.id) == []


def test_presenca_expira_sem_heartbeat(api, loja, settings):
    settings.PRESENCE_TTL_SECONDS = 1
    api.post(f'/api/projects/{loja.id}/presence')
    import time

    time.sleep(1.2)

    assert viewers(loja.id) == []


def test_heartbeat_publica_evento_de_presenca(api, loja):
    from hubflow.realtime.events import subscribe

    with subscribe(loja.id) as events:
        api.post(f'/api/projects/{loja.id}/presence')
        event = next(events)

    assert event['type'] == 'presence'
    assert [v['email'] for v in event['data']['viewers']] == ['ana@example.com']
