from datetime import timedelta

import pytest
from django.utils import timezone

from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db


def test_inicia_cronometro(api, card, user):
    response = api.post(f'/api/cards/{card.id}/timer/start')

    assert response.status_code == 201
    data = response.json()
    assert data['ended_at'] is None and data['is_running'] is True
    assert data['user']['email'] == 'ana@example.com'
    assert TimeEntry.objects.running_for(card).user == user


def test_iniciar_duas_vezes_retorna_400(api, card):
    api.post(f'/api/cards/{card.id}/timer/start')

    response = api.post(f'/api/cards/{card.id}/timer/start')

    assert response.status_code == 400
    assert 'cronômetro' in response.json()['detail'].lower()


def test_para_cronometro(api, card):
    api.post(f'/api/cards/{card.id}/timer/start')

    response = api.post(f'/api/cards/{card.id}/timer/stop')

    assert response.status_code == 200
    assert response.json()['ended_at'] is not None
    assert response.json()['hours'] >= 0


def test_parar_sem_cronometro_retorna_400(api, card):
    assert api.post(f'/api/cards/{card.id}/timer/stop').status_code == 400


def test_tempo_do_card_lista_entradas_total_e_aberto(api, card, user):
    start = timezone.now() - timedelta(hours=3)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=1))
    TimeEntry.objects.manual(card=card, user=user, hours=0.5, date=timezone.localdate(), note='Reunião')
    api.post(f'/api/cards/{card.id}/timer/start')

    response = api.get(f'/api/cards/{card.id}/time')

    assert response.status_code == 200
    data = response.json()
    assert len(data['entries']) == 3
    assert data['total_hours'] == 1.5
    assert data['running']['is_running'] is True
    assert [e['is_manual'] for e in data['entries']].count(True) == 1


def test_card_sem_tempo(api, card):
    data = api.get(f'/api/cards/{card.id}/time').json()

    assert data == {'entries': [], 'total_hours': 0.0, 'running': None}


def test_card_do_quadro_mostra_horas_e_cronometro(api, loja, card, user):
    start = timezone.now() - timedelta(hours=2)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=2))
    api.post(f'/api/cards/{card.id}/timer/start')

    board_card = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards'][0]

    assert board_card['time'] == {'hours': 2.0, 'running': True}


def test_horas_do_quadro_nao_multiplicam_com_checklist_e_anexos(api, loja, card, user):
    from hubflow.boards.models import ChecklistItem

    ChecklistItem.objects.create(card=card, text='a')
    ChecklistItem.objects.create(card=card, text='b')
    start = timezone.now() - timedelta(hours=2)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=1))
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=1))

    board_card = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards'][0]

    assert board_card['time']['hours'] == 2.0
    assert board_card['checklist'] == {'done': 0, 'total': 2}
