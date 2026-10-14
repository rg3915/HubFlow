import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import BOARD, CARD, PROJECTS
from tests.test_card_time import ENTRY, MANUAL, RUNNING

APP = PROJECTS[0] | {'id': 6, 'name': 'App', 'repo': 'app'}
APP_CARD = CARD | {'id': 30, 'project_id': 6, 'number': 1, 'title': 'Tela inicial'}
APP_BOARD = BOARD | {'columns': [{'key': 'doing', 'label': 'Em desenvolvimento', 'cards': [APP_CARD]}]}
OLD = ENTRY | {'id': 40, 'card_id': 30, 'started_at': '2026-10-01T08:00:00+00:00', 'ended_at': None, 'hours': 2}
NO_TIME = {'entries': [], 'total_hours': 0, 'running': None}


def card_time(*entries):
    return Response(200, json={'entries': list(entries), 'total_hours': 0, 'running': None})


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS + [APP]))
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))
    respx.get('http://api.test/api/projects/6/board').mock(return_value=Response(200, json=APP_BOARD))
    respx.get('http://api.test/api/cards/9/time').mock(return_value=card_time(ENTRY, RUNNING))
    respx.get('http://api.test/api/cards/10/time').mock(return_value=card_time(MANUAL))
    respx.get('http://api.test/api/cards/30/time').mock(return_value=card_time(OLD))


@respx.mock
def test_timesheets_junta_todos_os_projetos_em_ordem_decrescente(run):
    result = run('timesheets')

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert len(lines) == 4
    assert '14/10/2026' in lines[0] and 'rodando' in lines[0]
    assert 'Loja' in lines[0] and '#3 Corrigir login' in lines[0]
    assert '01/10/2026' in lines[-1] and 'App' in lines[-1] and '#1 Tela inicial' in lines[-1]
    assert '1h 30min' in result.output and 'ana@acme.com' in result.output


@respx.mock
def test_timesheets_filtra_por_projeto(run):
    board_app = respx.get('http://api.test/api/projects/6/board')

    result = run('timesheets', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'Loja' in result.output and 'App' not in result.output
    assert not board_app.called


@respx.mock
def test_timesheets_respeita_o_limite(run):
    result = run('timesheets', '--limit', '2')

    assert result.exit_code == 0, result.output
    assert len(result.output.splitlines()) == 2
    assert '01/10/2026' not in result.output


@respx.mock
def test_timesheets_sem_entradas(run):
    for card_id in (9, 10, 30):
        respx.get(f'http://api.test/api/cards/{card_id}/time').mock(return_value=Response(200, json=NO_TIME))

    result = run('timesheets')

    assert result.exit_code == 0, result.output
    assert 'Nenhum tempo registrado' in result.output


@respx.mock
def test_timesheets_com_projeto_desconhecido_falha(run):
    result = run('timesheets', '--project', 'Nada')

    assert result.exit_code == 1
    assert 'Nada' in result.output
