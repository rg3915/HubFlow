import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config

PROJECTS = [
    {
        'id': 5,
        'client_id': 1,
        'client_name': 'ACME',
        'name': 'Loja',
        'provider': 'github',
        'owner': 'acme',
        'repo': 'loja',
        'repository_url': 'https://github.com/acme/loja',
        'description': '',
        'emails': [],
        'is_active': True,
    },
]
CARD = {
    'id': 9,
    'project_id': 5,
    'number': 3,
    'title': 'Corrigir login',
    'description': '',
    'column': 'backlog',
    'position': 0,
}
DOING_CARD = CARD | {'id': 10, 'number': 4, 'title': 'Pagamento', 'column': 'doing'}
BOARD = {
    'project': {'id': 5, 'name': 'Loja', 'client_name': 'ACME'},
    'columns': [
        {'key': 'backlog', 'label': 'Backlog', 'cards': [CARD]},
        {'key': 'sprint', 'label': 'Sprint', 'cards': []},
        {'key': 'doing', 'label': 'Em desenvolvimento', 'cards': [DOING_CARD]},
        {'key': 'qa', 'label': 'QA', 'cards': []},
        {'key': 'done', 'label': 'Concluído', 'cards': []},
        {'key': 'archived', 'label': 'Arquivadas', 'cards': []},
    ],
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[]))


@respx.mock
def test_card_create_resolve_o_projeto_pelo_nome(run):
    route = respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=CARD))

    result = run('card', 'create', 'Corrigir login', '--project', 'Loja', '--description', 'Erro 500')

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {'title': 'Corrigir login', 'description': 'Erro 500'}
    assert '#3' in result.output and 'Corrigir login' in result.output


@respx.mock
def test_card_create_com_projeto_desconhecido_falha(run):
    result = run('card', 'create', 'X', '--project', 'Nada')

    assert result.exit_code == 1
    assert 'Nada' in result.output


@respx.mock
def test_card_list_mostra_o_quadro_por_coluna(run):
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))

    result = run('card', 'list', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'Backlog' in result.output and '#3' in result.output
    assert 'Em desenvolvimento' in result.output and '#4' in result.output
    assert 'Sprint' not in result.output  # colunas vazias não aparecem


@respx.mock
def test_card_list_filtra_por_coluna(run):
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))

    result = run('card', 'list', '--project', 'Loja', '--column', 'doing')

    assert '#4' in result.output and '#3' not in result.output


@respx.mock
def test_card_list_vazio(run):
    empty = BOARD | {'columns': [c | {'cards': []} for c in BOARD['columns']]}
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=empty))

    result = run('card', 'list', '--project', 'Loja')

    assert 'Nenhum card' in result.output


@respx.mock
def test_card_list_rejeita_coluna_desconhecida(run):
    result = run('card', 'list', '--project', 'Loja', '--column', 'limbo')

    assert result.exit_code != 0
