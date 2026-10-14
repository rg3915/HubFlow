import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import Client
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123')


def reset_link_parts(user):
    return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)


def reset(uid, token, password):
    data = {'uid': uid, 'token': token, 'password': password}
    return Client().post('/api/auth/password/reset', data, content_type='application/json')


def test_define_a_nova_senha(user):
    uid, token = reset_link_parts(user)

    response = reset(uid, token, 'novaSenha456')

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password('novaSenha456')


def test_token_so_pode_ser_usado_uma_vez(user):
    # RN-04
    uid, token = reset_link_parts(user)
    reset(uid, token, 'novaSenha456')

    response = reset(uid, token, 'outraSenha789')

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password('novaSenha456')


def test_token_invalido_retorna_400(user):
    uid, _ = reset_link_parts(user)

    assert reset(uid, 'token-falso', 'novaSenha456').status_code == 400


def test_uid_invalido_retorna_400(user):
    _, token = reset_link_parts(user)

    assert reset('xyz', token, 'novaSenha456').status_code == 400


def test_senha_fraca_retorna_400_com_motivo(user):
    # RN-02
    uid, token = reset_link_parts(user)

    response = reset(uid, token, '123')

    assert response.status_code == 400
    assert 'detail' in response.json()
    user.refresh_from_db()
    assert user.check_password('segredo123')


def test_nao_exige_token_de_api(user):
    uid, token = reset_link_parts(user)

    assert reset(uid, token, 'novaSenha456').status_code == 200
