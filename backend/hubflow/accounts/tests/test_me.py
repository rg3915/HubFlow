import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from hubflow.accounts.models import Token

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123', name='Ana')


def get_me(token=None):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    return Client().get('/api/auth/me', headers=headers)


def test_me_devolve_o_usuario_do_token(user):
    token = Token.objects.create(user=user)

    response = get_me(token.key)

    assert response.status_code == 200
    assert response.json() == {
        'id': user.id,
        'email': 'ana@example.com',
        'name': 'Ana',
        'first_name': 'Ana',
        'avatar_url': None,
    }


def test_sem_token_retorna_401(user):
    # RN-06
    assert get_me().status_code == 401


def test_token_invalido_retorna_401(user):
    assert get_me('nao-existe').status_code == 401


def test_token_de_usuario_inativo_retorna_401(user):
    token = Token.objects.create(user=user)
    user.is_active = False
    user.save()

    assert get_me(token.key).status_code == 401
