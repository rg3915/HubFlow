import pytest
from django.core import mail

from hubflow.boards.models import Card
from hubflow.boards.notifications import notify
from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme():
    return Client.objects.create(name='ACME', emails=['ti@acme.com', 'chefe@acme.com'])


@pytest.fixture
def loja(acme):
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


@pytest.fixture
def card(loja):
    return Card.objects.create(project=loja, title='Corrigir login')


def test_envia_para_os_emails_do_projeto(card, loja):
    # RN-40
    loja.emails = ['dev@acme.com']
    loja.save()

    notify('created', card)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['dev@acme.com']


def test_sem_emails_no_projeto_usa_os_do_cliente(card):
    notify('created', card)

    assert mail.outbox[0].to == ['ti@acme.com', 'chefe@acme.com']


def test_sem_emails_em_lugar_nenhum_nao_envia(card, loja, acme):
    acme.emails = []
    acme.save()

    notify('created', card)

    assert mail.outbox == []


def test_conteudo_do_email(card, settings):
    # RN-42
    settings.FRONTEND_URL = 'http://app.test'

    notify('created', card)

    message = mail.outbox[0]
    assert message.subject == '[HubFlow] ACME / Loja: novo card #1 Corrigir login'
    assert 'ACME' in message.body and 'Loja' in message.body
    assert '#1 Corrigir login' in message.body
    assert 'http://app.test/projects/' in message.body


def test_evento_movido_informa_origem_e_destino(card):
    notify('moved', card, from_column='backlog', to_column='qa')

    message = mail.outbox[0]
    assert 'movido' in message.subject
    assert 'Backlog' in message.body and 'QA' in message.body


def test_evento_concluido(card):
    notify('done', card)

    assert 'concluído' in mail.outbox[0].subject


def test_evento_desligado_no_projeto_nao_envia(card, loja):
    # RN-41
    loja.notify_on_created = False
    loja.save()

    notify('created', card)

    assert mail.outbox == []
