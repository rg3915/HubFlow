import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.clients.models import Client

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


def invite(api, **overrides):
    payload = {'email': 'nova@hubflow.com', 'name': 'Nova Pessoa', 'roles': ['Desenvolvedor']} | overrides
    return api.post('/api/users/invite', payload, **JSON)


def test_convite_cria_a_pessoa_com_papel_e_clientes_e_envia_o_link(api):
    acme = Client.objects.create(name='ACME')

    response = invite(api, client_ids=[acme.id])

    assert response.status_code == 201
    data = response.json()
    assert data['roles'] == ['Desenvolvedor'] and [c['name'] for c in data['clients']] == ['ACME']
    person = User.objects.get(email='nova@hubflow.com')
    assert not person.has_usable_password()
    assert len(mail.outbox) == 1 and mail.outbox[0].to == ['nova@hubflow.com']
    assert 'convite' in mail.outbox[0].subject.lower()
    uid, token = re.search(r'/reset-password/([^/]+)/(\S+)', mail.outbox[0].body).groups()

    reset = HttpClient().post(
        '/api/auth/password/reset', {'uid': uid, 'token': token, 'password': 'Senha-forte-123'}, **JSON
    )
    assert reset.status_code == 200
    login = {'email': 'nova@hubflow.com', 'password': 'Senha-forte-123'}
    assert HttpClient().post('/api/auth/login', login, **JSON).status_code == 200


def test_email_ja_cadastrado_retorna_400(api, user):
    response = invite(api, email=user.email.upper())

    assert response.status_code == 400
    assert len(mail.outbox) == 0


def test_papel_desconhecido_retorna_400(api):
    assert invite(api, roles=['Chefe']).status_code == 400
    assert not User.objects.filter(email='nova@hubflow.com').exists()


def test_sem_permissao_de_convidar_retorna_403(db):
    dev = User.objects.create_user(email='dev@hubflow.com', password='x')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=dev).key}'})

    assert invite(api).status_code == 403


def test_email_invalido_retorna_400(api):
    assert invite(api, email='nao-e-email').status_code == 400
