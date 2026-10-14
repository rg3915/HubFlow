import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from hubflow.accounts.models import Token

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123')


def logout(token):
    return Client().post('/api/auth/logout', headers={'Authorization': f'Bearer {token}'})


def test_logout_invalida_o_token(user):
    token = Token.objects.create(user=user)

    response = logout(token.key)

    assert response.status_code == 204
    assert not Token.objects.filter(key=token.key).exists()


def test_logout_mantem_os_outros_tokens_do_usuario(user):
    # RN-05
    phone = Token.objects.create(user=user)
    cli = Token.objects.create(user=user)

    logout(phone.key)

    assert Token.objects.filter(key=cli.key).exists()


def test_token_invalidado_nao_entra_mais(user):
    token = Token.objects.create(user=user)
    logout(token.key)

    assert Client().get('/api/auth/me', headers={'Authorization': f'Bearer {token.key}'}).status_code == 401


def test_logout_sem_token_retorna_401(user):
    assert Client().post('/api/auth/logout').status_code == 401
