import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.clients.models import Client

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


@pytest.fixture
def dev(db):
    dev = User.objects.create_user(email='dev@hubflow.com', password='x', name='Dev')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    return dev


def changes(api, **params):
    return api.get('/api/users/changes', params).json()


def test_cada_alteracao_registra_quem_quando_e_o_que(api, user, dev):
    acme = Client.objects.create(name='ACME')
    api.put(f'/api/users/{dev.id}/roles', {'roles': ['Gerente']}, **JSON)
    api.put(f'/api/users/{dev.id}/permissions', {'permissions': ['billing.view_payment']}, **JSON)
    api.put(f'/api/users/{dev.id}/clients', {'client_ids': [acme.id]}, **JSON)
    api.put(f'/api/users/{dev.id}/active', {'is_active': False}, **JSON)

    log = changes(api, user=dev.id)

    assert [(c['action'], c['before'], c['after']) for c in log] == [
        ('active', [True], [False]),
        ('clients', [], ['ACME']),
        ('permissions', [], ['billing.view_payment']),
        ('roles', ['Desenvolvedor'], ['Gerente']),
    ]
    assert {c['changed_by'] for c in log} == {user.email}
    assert all(c['user'] == dev.email and c['created'] for c in log)


def test_convite_fica_registrado(api):
    api.post('/api/users/invite', {'email': 'nova@hubflow.com', 'roles': ['Leitura']}, **JSON)

    assert [(c['action'], c['user'], c['after']) for c in changes(api)] == [
        ('invite', 'nova@hubflow.com', ['Leitura'])
    ]


def test_sem_mudanca_nao_registra(api, dev):
    api.put(f'/api/users/{dev.id}/roles', {'roles': ['Desenvolvedor']}, **JSON)

    assert changes(api) == []


def test_so_quem_gerencia_ve_o_registro(dev):
    api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=dev).key}'})

    assert api.get('/api/users/changes').status_code == 403
