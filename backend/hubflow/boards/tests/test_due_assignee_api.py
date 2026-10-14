from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def bob(db):
    return get_user_model().objects.create_user(email='bob@example.com', password='segredo123', name='Bob')


def test_card_nasce_sem_prazo_nem_responsavel(api, card):
    data = api.get(f'/api/cards/{card.id}').json()

    assert (data['due_date'], data['assignee']) == (None, None)


def test_define_prazo_e_responsavel(api, card, bob):
    body = {'title': card.title, 'due_date': '2026-10-20', 'assignee_id': bob.id}

    response = api.put(f'/api/cards/{card.id}', body, **JSON)

    assert response.status_code == 200
    data = response.json()
    assert data['due_date'] == '2026-10-20'
    assert data['assignee'] == {'id': bob.id, 'email': 'bob@example.com', 'name': 'Bob'}


def test_limpa_prazo_e_responsavel(api, card, bob):
    api.put(f'/api/cards/{card.id}', {'title': card.title, 'due_date': '2026-10-20', 'assignee_id': bob.id}, **JSON)

    response = api.put(f'/api/cards/{card.id}', {'title': card.title, 'due_date': None, 'assignee_id': None}, **JSON)

    assert (response.json()['due_date'], response.json()['assignee']) == (None, None)


def test_responsavel_inexistente_retorna_404(api, card):
    response = api.put(f'/api/cards/{card.id}', {'title': card.title, 'assignee_id': 999}, **JSON)

    assert response.status_code == 404


def test_data_invalida_retorna_422(api, card):
    response = api.put(f'/api/cards/{card.id}', {'title': card.title, 'due_date': 'amanhã'}, **JSON)

    assert response.status_code == 422


def test_cria_card_ja_com_prazo_e_responsavel(api, loja, bob):
    body = {'title': 'Com prazo', 'due_date': '2026-11-01', 'assignee_id': bob.id}

    response = api.post(f'/api/projects/{loja.id}/cards', body, **JSON)

    assert response.status_code == 201
    assert response.json()['assignee']['email'] == 'bob@example.com'


def test_quadro_marca_cards_vencidos(api, loja):
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)
    late = Card.objects.create(project=loja, title='Atrasado', due_date=yesterday)
    Card.objects.create(project=loja, title='No prazo', due_date=tomorrow)
    Card.objects.create(project=loja, title='Sem prazo')

    cards = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards']

    expected = [('Atrasado', True), ('No prazo', False), ('Sem prazo', False)]
    assert [(c['title'], c['is_overdue']) for c in cards] == expected
    assert cards[0]['id'] == late.id


def test_card_concluido_nao_conta_como_vencido(api, loja):
    card = Card.objects.create(project=loja, title='Feito', due_date=date.today() - timedelta(days=3), column='done')

    data = api.get(f'/api/cards/{card.id}').json()

    assert data['is_overdue'] is False
