import datetime
import json

import pytest
import respx
from httpx import Response

from hubflow_cli.client import format_hours
from hubflow_cli.config import save_config
from tests.test_card import BOARD, CARD, PROJECTS

USER = {'id': 1, 'email': 'ana@acme.com', 'name': 'Ana'}
ENTRY = {
    'id': 21,
    'card_id': 9,
    'user': USER,
    'started_at': '2026-10-14T09:00:00+00:00',
    'ended_at': '2026-10-14T10:30:00+00:00',
    'note': '',
    'is_manual': False,
    'is_running': False,
    'hours': 1.5,
}
RUNNING = ENTRY | {
    'id': 22,
    'started_at': '2026-10-14T11:00:00+00:00',
    'ended_at': None,
    'is_running': True,
    'hours': 0.25,
}
MANUAL = ENTRY | {'id': 23, 'note': 'reunião', 'is_manual': True, 'hours': 0.75}
CARD_TIME = {'entries': [ENTRY, MANUAL, RUNNING], 'total_hours': 2.5, 'running': RUNNING}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))


@pytest.mark.parametrize('hours, text', [(0.75, '0h 45min'), (1.5, '1h 30min'), (2.0, '2h'), (0, '0h')])
def test_format_hours(hours, text):
    assert format_hours(hours) == text


@respx.mock
def test_card_start_move_e_abre_o_cronometro(run):
    respx.post('http://api.test/api/cards/9/start').mock(return_value=Response(200, json=CARD | {'column': 'doing'}))
    timer = respx.post('http://api.test/api/cards/9/timer/start').mock(return_value=Response(201, json=RUNNING))

    result = run('card', 'start', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert timer.called
    assert 'Em desenvolvimento' in result.output and 'cronômetro rodando' in result.output


@respx.mock
def test_card_start_com_cronometro_ja_aberto_avisa_e_segue(run):
    respx.post('http://api.test/api/cards/9/start').mock(return_value=Response(200, json=CARD | {'column': 'doing'}))
    respx.post('http://api.test/api/cards/9/timer/start').mock(
        return_value=Response(400, json={'detail': 'Já existe um cronômetro aberto neste card.'})
    )

    result = run('card', 'start', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'cronômetro já estava aberto' in result.output
    assert 'Em desenvolvimento' in result.output and 'cronômetro rodando' in result.output


@respx.mock
def test_card_stop_mostra_a_sessao_e_o_total(run):
    stop = respx.post('http://api.test/api/cards/9/timer/stop').mock(return_value=Response(200, json=ENTRY))
    respx.get('http://api.test/api/cards/9/time').mock(return_value=Response(200, json=CARD_TIME))

    result = run('card', 'stop', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert stop.called
    assert '1h 30min' in result.output and '2h 30min' in result.output


@respx.mock
def test_card_stop_sem_cronometro_aberto_falha_com_mensagem_amigavel(run):
    respx.post('http://api.test/api/cards/9/timer/stop').mock(
        return_value=Response(400, json={'detail': 'Não há cronômetro aberto neste card.'})
    )

    result = run('card', 'stop', '3', '--project', 'Loja')

    assert result.exit_code == 1
    assert 'cronômetro aberto' in result.output and '#3' in result.output


@respx.mock
def test_card_log_registra_horas_na_data_informada(run):
    route = respx.post('http://api.test/api/cards/9/time-entries').mock(return_value=Response(201, json=MANUAL))

    args = ('--project', 'Loja', '--hours', '0.75', '--date', '2026-10-14', '--note', 'reunião')
    result = run('card', 'log', '3', *args)

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {'hours': 0.75, 'date': '2026-10-14', 'note': 'reunião'}
    assert '0h 45min' in result.output and '#3' in result.output


@respx.mock
def test_card_log_sem_data_usa_hoje(run):
    route = respx.post('http://api.test/api/cards/9/time-entries').mock(return_value=Response(201, json=MANUAL))

    run('card', 'log', '3', '--project', 'Loja', '--hours', '1')

    body = json.loads(route.calls.last.request.read())
    assert body['date'] == datetime.date.today().isoformat() and body['note'] == ''


@respx.mock
def test_card_log_rejeita_horas_nao_positivas(run):
    route = respx.post('http://api.test/api/cards/9/time-entries')

    result = run('card', 'log', '3', '--project', 'Loja', '--hours', '0')

    assert result.exit_code == 2
    assert not route.called


@respx.mock
def test_card_log_rejeita_data_invalida(run):
    route = respx.post('http://api.test/api/cards/9/time-entries')

    result = run('card', 'log', '3', '--project', 'Loja', '--hours', '1', '--date', '14/10/2026')

    assert result.exit_code == 2
    assert 'AAAA-MM-DD' in result.output
    assert not route.called


@respx.mock
def test_card_time_lista_as_entradas_e_o_total(run):
    respx.get('http://api.test/api/cards/9/time').mock(return_value=Response(200, json=CARD_TIME))

    result = run('card', 'time', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert '14/10/2026' in result.output
    assert '1h 30min' in result.output and 'ana@acme.com' in result.output
    assert 'manual' in result.output and 'reunião' in result.output
    assert '(rodando)' in result.output
    assert 'Total' in result.output and '2h 30min' in result.output


@respx.mock
def test_card_time_sem_entradas(run):
    respx.get('http://api.test/api/cards/9/time').mock(
        return_value=Response(200, json={'entries': [], 'total_hours': 0, 'running': None})
    )

    result = run('card', 'time', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'Nenhum tempo registrado' in result.output


@respx.mock
def test_card_time_numero_inexistente_falha(run):
    result = run('card', 'time', '99', '--project', 'Loja')

    assert result.exit_code == 1
    assert '#99' in result.output
