import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from hubflow.accounts.models import Token

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123')


def login(email, password):
    return Client().post('/api/auth/login', {'email': email, 'password': password}, content_type='application/json')


def test_login_retorna_token(user):
    response = login('ana@example.com', 'segredo123')

    assert response.status_code == 200
    token = response.json()['token']
    assert Token.objects.get(key=token).user == user


def test_login_nao_diferencia_maiusculas_no_email(user):
    assert login('ANA@EXAMPLE.COM', 'segredo123').status_code == 200


def test_login_com_senha_errada_retorna_401(user):
    response = login('ana@example.com', 'errada')

    assert response.status_code == 401
    assert Token.objects.count() == 0


def test_login_de_usuario_inativo_retorna_401(user):
    user.is_active = False
    user.save()

    assert login('ana@example.com', 'segredo123').status_code == 401


def test_cada_login_gera_um_token_proprio(user):
    # RN-05: um token por dispositivo.
    first = login('ana@example.com', 'segredo123').json()['token']
    second = login('ana@example.com', 'segredo123').json()['token']

    assert first != second
    assert Token.objects.filter(user=user).count() == 2
