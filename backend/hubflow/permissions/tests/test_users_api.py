import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.clients.models import Client
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


@pytest.fixture
def admin_api(db):
    admin = User.objects.create_superuser(email='admin@hubflow.com', password='x', name='Admin')
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=admin).key}'})


@pytest.fixture
def dev(db):
    dev = User.objects.create_user(email='dev@hubflow.com', password='x', name='Dev Silva')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    return dev


def test_me_devolve_papeis_e_permissoes_efetivas(api, user):
    user.groups.add(Group.objects.get(name='Gerente'))

    data = api.get('/api/auth/me').json()

    assert data['roles'] == ['Gerente']
    assert 'boards.change_card' in data['permissions'] and 'accounts.change_user' not in data['permissions']
    assert data['is_superuser'] is False


def test_lista_usuarios_com_papeis_permissoes_e_clientes(admin_api, dev):
    acme = Client.objects.create(name='ACME')
    Membership.objects.create(user=dev, client=acme)

    response = admin_api.get('/api/users/manage')

    assert response.status_code == 200
    row = next(u for u in response.json() if u['email'] == 'dev@hubflow.com')
    assert row['roles'] == ['Desenvolvedor'] and row['clients'] == [{'id': acme.id, 'name': 'ACME'}]
    assert 'boards.add_card' in row['permissions'] and row['extra_permissions'] == []
    assert row['is_active'] is True


def test_quem_nao_gerencia_usuarios_recebe_403(api, dev):
    assert api.get('/api/users/manage').status_code == 403
    assert api.put(f'/api/users/{dev.id}/roles', {'roles': ['Gerente']}, **JSON).status_code == 403


def test_atribui_papeis(admin_api, dev):
    response = admin_api.put(f'/api/users/{dev.id}/roles', {'roles': ['Gerente', 'Financeiro']}, **JSON)

    assert response.status_code == 200
    assert sorted(response.json()['roles']) == ['Financeiro', 'Gerente']
    assert 'billing.change_payment' in response.json()['permissions']


def test_papel_desconhecido_retorna_400(admin_api, dev):
    assert admin_api.put(f'/api/users/{dev.id}/roles', {'roles': ['Rei']}, **JSON).status_code == 400


def test_liga_e_desliga_permissao_por_pessoa(admin_api, dev):
    response = admin_api.put(f'/api/users/{dev.id}/permissions', {'permissions': ['billing.view_payment']}, **JSON)

    assert response.status_code == 200
    assert response.json()['extra_permissions'] == ['billing.view_payment']
    assert 'billing.view_payment' in response.json()['permissions']

    response = admin_api.put(f'/api/users/{dev.id}/permissions', {'permissions': []}, **JSON)
    assert 'billing.view_payment' not in response.json()['permissions']


def test_permissao_fora_do_catalogo_retorna_400(admin_api, dev):
    response = admin_api.put(f'/api/users/{dev.id}/permissions', {'permissions': ['auth.add_group']}, **JSON)

    assert response.status_code == 400


def test_vincula_clientes(admin_api, dev):
    acme, beta = Client.objects.create(name='ACME'), Client.objects.create(name='Beta')

    response = admin_api.put(f'/api/users/{dev.id}/clients', {'client_ids': [beta.id, acme.id]}, **JSON)

    assert [c['name'] for c in response.json()['clients']] == ['ACME', 'Beta']
    assert Membership.objects.filter(user=dev).count() == 2


def test_desativa_e_reativa_usuario(admin_api, dev):
    response = admin_api.put(f'/api/users/{dev.id}/active', {'is_active': False}, **JSON)

    assert response.json()['is_active'] is False
    dev.refresh_from_db()
    assert dev.is_active is False


def test_admin_nao_desativa_a_si_mesmo(admin_api):
    admin = User.objects.get(email='admin@hubflow.com')

    assert admin_api.put(f'/api/users/{admin.id}/active', {'is_active': False}, **JSON).status_code == 400


def test_lista_papeis_e_catalogo_de_permissoes(admin_api):
    data = admin_api.get('/api/users/catalog').json()

    assert [r['name'] for r in data['roles']][:2] == ['Administrador', 'Gerente']
    assert any(
        p['code'] == 'boards.change_card' and p['label'] == 'Editar e mover qualquer card' for p in data['permissions']
    )
