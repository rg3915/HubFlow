from datetime import timedelta

import pytest
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def spend(card, user, hours):
    start = timezone.now() - timedelta(hours=hours + 1)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=hours))


def done_card(loja, user, title, hours):
    card = Card.objects.create(project=loja, title=title, column='done')
    spend(card, user, hours)
    return card


def test_card_nasce_sem_estimativa(api, card):
    data = api.get(f'/api/cards/{card.id}').json()

    assert data['estimate_hours'] is None


def test_define_estimativa(api, card):
    response = api.put(f'/api/cards/{card.id}', {'title': card.title, 'estimate_hours': 4}, **JSON)

    assert response.status_code == 200
    assert response.json()['estimate_hours'] == 4.0


def test_estimativa_negativa_retorna_422(api, card):
    assert api.put(f'/api/cards/{card.id}', {'title': card.title, 'estimate_hours': -1}, **JSON).status_code == 422


def test_progresso_gasto_x_estimado(api, card, user):
    api.put(f'/api/cards/{card.id}', {'title': card.title, 'estimate_hours': 4}, **JSON)
    spend(card, user, 3)

    progress = api.get(f'/api/cards/{card.id}').json()['progress']

    assert progress == {'spent_hours': 3.0, 'estimate_hours': 4.0, 'percent': 75, 'source': 'card'}


def test_sem_estimativa_usa_a_mediana_das_concluidas_do_projeto(api, loja, card, user):
    # RN-75
    for title, hours in (('A', 2), ('B', 4), ('C', 9)):
        done_card(loja, user, title, hours)
    spend(card, user, 2)

    progress = api.get(f'/api/cards/{card.id}').json()['progress']

    assert progress == {'spent_hours': 2.0, 'estimate_hours': 4.0, 'percent': 50, 'source': 'median'}


def test_sem_estimativa_e_sem_historico_nao_tem_percentual(api, card, user):
    spend(card, user, 1)

    progress = api.get(f'/api/cards/{card.id}').json()['progress']

    assert progress == {'spent_hours': 1.0, 'estimate_hours': None, 'percent': None, 'source': None}


def test_percentual_passa_de_100_quando_estoura(api, card, user):
    api.put(f'/api/cards/{card.id}', {'title': card.title, 'estimate_hours': 1}, **JSON)
    spend(card, user, 2)

    assert api.get(f'/api/cards/{card.id}').json()['progress']['percent'] == 200


def test_quadro_traz_o_progresso(api, loja, card, user):
    api.put(f'/api/cards/{card.id}', {'title': card.title, 'estimate_hours': 2}, **JSON)
    spend(card, user, 1)

    board_card = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards'][0]

    assert board_card['progress']['percent'] == 50
