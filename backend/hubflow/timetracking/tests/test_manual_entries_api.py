import pytest
from django.contrib.auth import get_user_model
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def log(api, card, hours=1.5, date='2026-10-13', note='Reunião'):
    return api.post(f'/api/cards/{card.id}/time-entries', {'hours': hours, 'date': date, 'note': note}, **JSON)


def test_lanca_horas_manualmente(api, card, user):
    # RN-72
    response = log(api, card)

    assert response.status_code == 201
    data = response.json()
    assert (data['hours'], data['is_manual'], data['note']) == (1.5, True, 'Reunião')
    assert data['started_at'].startswith('2026-10-13')
    assert TimeEntry.objects.get(id=data['id']).user == user


def test_horas_devem_ser_positivas(api, card):
    assert log(api, card, hours=0).status_code == 422
    assert log(api, card, hours=-1).status_code == 422


def test_data_invalida_retorna_422(api, card):
    assert log(api, card, date='13/10/2026').status_code == 422


def test_edita_a_propria_entrada(api, card):
    entry_id = log(api, card).json()['id']

    response = api.put(f'/api/time-entries/{entry_id}', {'hours': 2, 'date': '2026-10-12', 'note': 'Ajuste'}, **JSON)

    assert response.status_code == 200
    assert response.json()['hours'] == 2.0
    assert response.json()['started_at'].startswith('2026-10-12')


def test_dono_exclui_a_propria_entrada(api, card):
    # RN-73
    entry_id = log(api, card).json()['id']

    assert api.delete(f'/api/time-entries/{entry_id}').status_code == 204
    assert not TimeEntry.objects.filter(id=entry_id).exists()


def test_outro_usuario_nao_edita_nem_exclui(api, card):
    # RN-73
    entry_id = log(api, card).json()['id']
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123')
    bob_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=bob).key}'})

    assert bob_api.delete(f'/api/time-entries/{entry_id}').status_code == 403
    assert bob_api.put(f'/api/time-entries/{entry_id}', {'hours': 1, 'date': '2026-10-13'}, **JSON).status_code == 403
    assert TimeEntry.objects.filter(id=entry_id).exists()


def test_cronometro_fechado_tambem_so_o_dono_apaga(api, card, user):
    # RN-73 vale para o cronômetro: quem iniciou e finalizou.
    api.post(f'/api/cards/{card.id}/timer/start')
    entry_id = api.post(f'/api/cards/{card.id}/timer/stop').json()['id']
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123')
    bob_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=bob).key}'})

    assert bob_api.delete(f'/api/time-entries/{entry_id}').status_code == 403
    assert api.delete(f'/api/time-entries/{entry_id}').status_code == 204


def test_cronometro_aberto_nao_pode_ser_apagado(api, card):
    entry_id = api.post(f'/api/cards/{card.id}/timer/start').json()['id']

    response = api.delete(f'/api/time-entries/{entry_id}')

    assert response.status_code == 400
