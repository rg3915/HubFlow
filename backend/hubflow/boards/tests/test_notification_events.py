import pytest
from django.core import mail

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def loja(db):
    acme = Client.objects.create(name='ACME', emails=['ti@acme.com'])
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


@pytest.fixture
def card(loja):
    card = Card.objects.create(project=loja, title='Corrigir login')
    mail.outbox.clear()
    return card


def test_criar_card_pela_api_avisa(api, loja):
    api.post(f'/api/projects/{loja.id}/cards', {'title': 'Novo'}, content_type='application/json')

    assert len(mail.outbox) == 1
    assert 'novo card' in mail.outbox[0].subject


def test_mover_card_avisa_com_origem_e_destino(api, card):
    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, content_type='application/json')

    assert len(mail.outbox) == 1
    assert 'card movido' in mail.outbox[0].subject
    assert 'Backlog' in mail.outbox[0].body and 'QA' in mail.outbox[0].body


def test_mover_para_concluido_avisa_como_concluido(api, card):
    api.post(f'/api/cards/{card.id}/move', {'column': 'done'}, content_type='application/json')

    assert len(mail.outbox) == 1
    assert 'card concluído' in mail.outbox[0].subject


def test_iniciar_card_avisa_como_movido(api, card):
    api.post(f'/api/cards/{card.id}/start')

    assert 'card movido' in mail.outbox[0].subject


def test_reordenar_na_mesma_coluna_nao_avisa(api, loja, card):
    Card.objects.create(project=loja, title='Outro')
    mail.outbox.clear()

    api.post(f'/api/cards/{card.id}/move', {'column': 'backlog', 'position': 1}, content_type='application/json')

    assert mail.outbox == []


def test_evento_desligado_nao_avisa(api, loja, card):
    loja.notify_on_moved = False
    loja.save()

    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, content_type='application/json')

    assert mail.outbox == []


def test_arquivar_nao_avisa(api, card):
    api.post(f'/api/cards/{card.id}/archive')

    assert mail.outbox == []
