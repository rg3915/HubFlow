import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import CARD, PROJECTS
from tests.test_sprint import SPRINT

OPEN = SPRINT | {'id': 3, 'number': 2}
CLOSED = SPRINT | {'id': 2, 'number': 1, 'is_open': False}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))


def body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_sem_sprint_e_sem_nenhuma_cadastrada_cria_sem_perguntar(run):
    # RN-61: a API cria a sprint 1 sozinha.
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[]))
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'X', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'sprint_id' not in body(route)
    assert 'nova sprint' not in result.output.lower()


@respx.mock
def test_com_sprint_aberta_pergunta_e_nao_responde_usa_a_ultima(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[OPEN, CLOSED]))
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'X', '--project', 'Loja', input='\n')

    assert result.exit_code == 0, result.output
    assert 'Criar uma nova sprint' in result.output
    assert body(route)['sprint_id'] == 3


@respx.mock
def test_responder_sim_cria_a_sprint_e_usa_a_nova(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[OPEN]))
    new_sprint = respx.post('http://api.test/api/projects/5/sprints').mock(
        return_value=Response(201, json=SPRINT | {'id': 9, 'number': 3})
    )
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'X', '--project', 'Loja', input='s\n')

    assert result.exit_code == 0, result.output
    assert new_sprint.called
    assert body(route)['sprint_id'] == 9
    assert 'Sprint 3' in result.output


@respx.mock
def test_opcao_sprint_pelo_numero_nao_pergunta(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[OPEN, CLOSED]))
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'X', '--project', 'Loja', '--sprint', '1')

    assert result.exit_code == 0, result.output
    assert 'Criar uma nova sprint' not in result.output
    assert body(route)['sprint_id'] == 2


@respx.mock
def test_opcao_sprint_inexistente_falha(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[OPEN]))

    result = run('card', 'create', 'X', '--project', 'Loja', '--sprint', '7')

    assert result.exit_code == 1
    assert 'Sprint 7' in result.output


@respx.mock
def test_no_input_usa_a_ultima_sem_perguntar(run):
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[OPEN]))
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'X', '--project', 'Loja', '--no-input')

    assert result.exit_code == 0, result.output
    assert 'Criar uma nova sprint' not in result.output
    assert body(route)['sprint_id'] == 3
