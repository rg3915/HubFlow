import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import BOARD, CARD, PROJECTS


def moved_to(column):
    return Response(200, json=CARD | {'column': column})


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))


@respx.mock
def test_card_move_resolve_o_card_pelo_numero_no_projeto(run):
    route = respx.post('http://api.test/api/cards/9/move').mock(return_value=moved_to('qa'))

    result = run('card', 'move', '3', '--project', 'Loja', '--to', 'qa', '--position', '0')

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {'column': 'qa', 'position': 0}
    assert 'QA' in result.output and '#3' in result.output


@respx.mock
def test_card_move_sem_posicao_vai_para_o_fim(run):
    route = respx.post('http://api.test/api/cards/9/move').mock(return_value=moved_to('done'))

    run('card', 'move', '3', '--project', 'Loja', '--to', 'done')

    assert json.loads(route.calls.last.request.read()) == {'column': 'done', 'position': None}


@respx.mock
def test_card_move_rejeita_coluna_desconhecida(run):
    result = run('card', 'move', '3', '--project', 'Loja', '--to', 'limbo')

    assert result.exit_code != 0


@respx.mock
def test_card_move_numero_inexistente_falha(run):
    result = run('card', 'move', '99', '--project', 'Loja', '--to', 'qa')

    assert result.exit_code == 1
    assert '#99' in result.output


@respx.mock
def test_card_start_move_para_em_desenvolvimento(run):
    route = respx.post('http://api.test/api/cards/9/start').mock(return_value=moved_to('doing'))

    result = run('card', 'start', '3', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert route.called
    assert 'Em desenvolvimento' in result.output
