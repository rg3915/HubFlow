import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from hubflow.accounts.models import Token

pytestmark = pytest.mark.django_db

CLI = {'X-HubFlow-Client': 'cli'}


def login(email, headers=None):
    payload = {'email': email, 'password': 'segredo123'}
    return Client(headers=headers).post('/api/auth/login', payload, content_type='application/json')


@pytest.fixture
def reader():
    person = get_user_model().objects.create_user(email='leitura@hubflow.com', password='segredo123')
    person.groups.add(Group.objects.get(name='Leitura'))
    return person


def test_login_pela_cli_marca_o_token(user):
    response = login(user.email, CLI)

    assert response.status_code == 200
    assert Token.objects.get(key=response.json()['token']).is_cli is True


def test_login_pelo_site_nao_marca_o_token(user):
    assert Token.objects.get(key=login(user.email).json()['token']).is_cli is False


def test_sem_permissao_nao_entra_pela_cli(reader):
    response = login(reader.email, CLI)

    assert response.status_code == 403
    assert 'CLI' in response.json()['detail']
    assert Token.objects.count() == 0


def test_sem_permissao_entra_pelo_site(reader):
    assert login(reader.email).status_code == 200


def test_token_da_cli_para_de_valer_quando_a_permissao_e_retirada(user):
    key = login(user.email, CLI).json()['token']
    user.groups.clear()
    user.groups.add(Group.objects.get(name='Leitura'))

    assert Client(headers={'Authorization': f'Bearer {key}'}).get('/api/auth/me').status_code == 401
