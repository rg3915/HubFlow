import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from hubflow.accounts.models import Token

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123')


@pytest.fixture
def token(user):
    return Token.objects.create(user=user).key


def change(token, current, new):
    data = {'current_password': current, 'new_password': new}
    headers = {'Authorization': f'Bearer {token}'}
    return Client().post('/api/auth/password/change', data, content_type='application/json', headers=headers)


def test_troca_a_senha(user, token):
    response = change(token, 'segredo123', 'novaSenha456')

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password('novaSenha456')


def test_senha_atual_errada_retorna_400(user, token):
    response = change(token, 'errada', 'novaSenha456')

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password('segredo123')


def test_senha_nova_fraca_retorna_400(user, token):
    # RN-02
    response = change(token, 'segredo123', '123')

    assert response.status_code == 400
    assert 'detail' in response.json()


def test_token_atual_continua_valido_apos_a_troca(user, token):
    change(token, 'segredo123', 'novaSenha456')

    assert Client().get('/api/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 200


def test_exige_login(user):
    assert change('invalido', 'segredo123', 'novaSenha456').status_code == 401
