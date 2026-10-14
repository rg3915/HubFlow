import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import BOARD, CARD, PROJECTS

FIELDS = [
    {'id': 1, 'name': 'Prioridade', 'kind': 'select', 'options': ['Alta', 'Baixa'], 'required': True, 'position': 0},
    {'id': 2, 'name': 'Pontos', 'kind': 'number', 'options': [], 'required': False, 'position': 1},
    {'id': 3, 'name': 'Urgente', 'kind': 'bool', 'options': [], 'required': False, 'position': 2},
]
FULL = CARD | {'assignee': None, 'due_date': None, 'estimate_hours': 4.0, 'sprint': None, 'custom_values': {}}


@pytest.fixture(autouse=True)
def api():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    with respx.mock:
        respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
        respx.get('http://api.test/api/projects/5/fields').mock(return_value=Response(200, json=FIELDS))
        respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[]))
        yield


def test_field_list(run):
    result = run('project', 'field', 'list', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'Prioridade  seleção (Alta, Baixa)  obrigatório' in result.output
    assert 'Pontos  número' in result.output


def test_field_add_selecao_obrigatoria(run):
    route = respx.post('http://api.test/api/projects/5/fields').mock(return_value=Response(201, json=FIELDS[0]))

    result = run(
        'project',
        'field',
        'add',
        'Loja',
        'Prioridade',
        '--kind',
        'select',
        '--option',
        'Alta',
        '--option',
        'Baixa',
        '--required',
    )

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {
        'name': 'Prioridade',
        'kind': 'select',
        'options': ['Alta', 'Baixa'],
        'required': True,
    }
    assert 'Campo Prioridade criado em Loja.' in result.output


def test_field_remove(run):
    route = respx.delete('http://api.test/api/fields/2').mock(return_value=Response(204))

    result = run('project', 'field', 'remove', 'Loja', 'pontos')

    assert result.exit_code == 0 and route.called


def test_card_create_com_campos_convertidos_pelo_tipo(run):
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=FULL))

    result = run(
        'card', 'create', 'Login', '--project', 'Loja', '--no-input',
        '--field', 'Prioridade=Alta', '--field', 'pontos=2,5', '--field', 'Urgente=sim',
    )  # fmt: skip

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read())['fields'] == {'1': 'Alta', '2': 2.5, '3': True}


def test_campo_desconhecido_da_dica(run):
    result = run('card', 'create', 'Login', '--project', 'Loja', '--no-input', '--field', 'Cor=azul')

    assert result.exit_code == 1
    assert 'hubflow project field list Loja' in result.output


def test_card_fields_mostra_e_altera_mantendo_o_resto(run):
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))
    respx.get('http://api.test/api/cards/9').mock(
        return_value=Response(200, json=FULL | {'custom_values': {'1': 'Alta'}})
    )
    route = respx.put('http://api.test/api/cards/9').mock(
        return_value=Response(200, json=FULL | {'custom_values': {'1': 'Baixa'}})
    )

    result = run('card', 'fields', '3', '--project', 'Loja', '--field', 'Prioridade=Baixa')

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.read())
    assert body['fields'] == {'1': 'Baixa'} and body['estimate_hours'] == 4.0
    assert 'Prioridade: Baixa' in result.output
