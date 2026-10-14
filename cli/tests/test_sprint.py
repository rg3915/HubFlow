import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS

SPRINT = {
    'id': 3,
    'project_id': 5,
    'number': 2,
    'name': 'Checkout',
    'milestone': None,
    'start_date': None,
    'end_date': None,
    'is_open': True,
    'closed_at': None,
    'cards_count': 4,
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))


def body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_sprint_create(run):
    route = respx.post('http://api.test/api/projects/5/sprints').mock(return_value=Response(201, json=SPRINT))

    result = run('sprint', 'create', '--project', 'Loja', '--name', 'Checkout', '--start', '2026-10-13')

    assert result.exit_code == 0, result.output
    assert body(route) == {'name': 'Checkout', 'milestone_id': None, 'start_date': '2026-10-13', 'end_date': None}
    assert 'Sprint 2' in result.output


@respx.mock
def test_sprint_create_rejeita_data_invalida(run):
    result = run('sprint', 'create', '--project', 'Loja', '--start', '13/10/2026')

    assert result.exit_code != 0
    assert 'AAAA-MM-DD' in result.output


@respx.mock
def test_sprint_list(run):
    closed = SPRINT | {'id': 2, 'number': 1, 'name': '', 'is_open': False, 'cards_count': 7}
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[SPRINT, closed]))

    result = run('sprint', 'list', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'Sprint 2' in result.output and 'Checkout' in result.output and '4 cards' in result.output
    assert 'Sprint 1' in result.output and 'fechada' in result.output


@respx.mock
def test_sprint_list_vazia(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[]))

    result = run('sprint', 'list', '--project', 'Loja')

    assert 'Nenhuma sprint' in result.output


@respx.mock
def test_sprint_close_pelo_numero(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[SPRINT]))
    closed = Response(200, json=SPRINT | {'is_open': False})
    route = respx.post('http://api.test/api/sprints/3/close').mock(return_value=closed)

    result = run('sprint', 'close', '2', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert route.called
    assert 'fechada' in result.output


@respx.mock
def test_sprint_close_numero_inexistente(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[SPRINT]))

    result = run('sprint', 'close', '9', '--project', 'Loja')

    assert result.exit_code == 1
    assert 'Sprint 9' in result.output
