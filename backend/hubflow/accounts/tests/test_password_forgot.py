import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='ana@example.com', password='segredo123')


def forgot(email):
    return Client().post('/api/auth/password/forgot', {'email': email}, content_type='application/json')


def test_envia_email_com_link_de_redefinicao(user, settings):
    settings.FRONTEND_URL = 'http://app.test'

    response = forgot('ana@example.com')

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['ana@example.com']
    assert re.search(r'http://app\.test/reset-password/[\w-]+/[\w-]+', message.body)


def test_email_desconhecido_responde_200_sem_enviar(user):
    # RN-03: não revela quem está cadastrado.
    response = forgot('ninguem@example.com')

    assert response.status_code == 200
    assert mail.outbox == []


def test_nao_diferencia_maiusculas_no_email(user):
    forgot('ANA@EXAMPLE.COM')

    assert len(mail.outbox) == 1


def test_usuario_inativo_nao_recebe_email(user):
    user.is_active = False
    user.save()

    forgot('ana@example.com')

    assert mail.outbox == []


def test_nao_exige_token():
    assert forgot('x@example.com').status_code == 200
