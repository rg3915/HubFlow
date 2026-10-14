import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import BOARD, CARD, PROJECTS

LABELS = [
    {'id': 1, 'project_id': 5, 'name': 'bug', 'color': '#a33a2e'},
    {'id': 2, 'project_id': 5, 'name': 'ui', 'color': '#245e7d'},
]
USERS = [
    {'id': 1, 'email': 'ana@example.com', 'name': 'Ana'},
    {'id': 2, 'email': 'bob@example.com', 'name': 'Bob'},
]
FULL_CARD = CARD | {
    'labels': [LABELS[0]],
    'due_date': None,
    'assignee': None,
    'is_overdue': False,
    'checklist': {'done': 0, 'total': 0},
    'attachments_count': 0,
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/projects/5/board').mock(return_value=Response(200, json=BOARD))
    respx.get('http://api.test/api/projects/5/labels').mock(return_value=Response(200, json=LABELS))
    respx.get('http://api.test/api/users').mock(return_value=Response(200, json=USERS))
    respx.get('http://api.test/api/cards/9').mock(return_value=Response(200, json=FULL_CARD))


def body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_comment_cria_comentario(run):
    route = respx.post('http://api.test/api/cards/9/comments').mock(
        return_value=Response(201, json={'id': 1, 'card_id': 9, 'text': 'Feito', 'mentions': []})
    )

    result = run('card', 'comment', '3', '--project', 'Loja', 'Feito')

    assert result.exit_code == 0, result.output
    assert body(route) == {'text': 'Feito'}
    assert '#3' in result.output


@respx.mock
def test_label_adiciona_e_remove_pelo_nome(run):
    route = respx.put('http://api.test/api/cards/9/labels').mock(
        return_value=Response(200, json=FULL_CARD | {'labels': [LABELS[1]]})
    )

    result = run('card', 'label', '3', '--project', 'Loja', '--add', 'ui', '--remove', 'bug')

    assert result.exit_code == 0, result.output
    assert body(route) == {'label_ids': [2]}
    assert 'ui' in result.output


@respx.mock
def test_label_desconhecida_falha_com_dica(run):
    result = run('card', 'label', '3', '--project', 'Loja', '--add', 'urgente')

    assert result.exit_code == 1
    assert 'urgente' in result.output and 'bug, ui' in result.output


@respx.mock
def test_assign_define_o_responsavel_pelo_email(run):
    route = respx.put('http://api.test/api/cards/9').mock(
        return_value=Response(200, json=FULL_CARD | {'assignee': USERS[1]})
    )

    result = run('card', 'assign', '3', '--project', 'Loja', '--to', 'bob@example.com')

    assert result.exit_code == 0, result.output
    sent = body(route)
    assert sent['assignee_id'] == 2 and sent['title'] == 'Corrigir login' and sent['due_date'] is None
    assert 'Bob' in result.output


@respx.mock
def test_assign_sem_to_limpa_o_responsavel(run):
    route = respx.put('http://api.test/api/cards/9').mock(return_value=Response(200, json=FULL_CARD))

    result = run('card', 'assign', '3', '--project', 'Loja', '--clear')

    assert result.exit_code == 0, result.output
    assert body(route)['assignee_id'] is None


@respx.mock
def test_assign_usuario_desconhecido_falha(run):
    result = run('card', 'assign', '3', '--project', 'Loja', '--to', 'zeca@example.com')

    assert result.exit_code == 1
    assert 'zeca@example.com' in result.output


@respx.mock
def test_due_define_o_prazo(run):
    route = respx.put('http://api.test/api/cards/9').mock(
        return_value=Response(200, json=FULL_CARD | {'due_date': '2026-10-20'})
    )

    result = run('card', 'due', '3', '--project', 'Loja', '2026-10-20')

    assert result.exit_code == 0, result.output
    assert body(route)['due_date'] == '2026-10-20'
    assert '20/10/2026' in result.output


@respx.mock
def test_due_rejeita_data_invalida(run):
    result = run('card', 'due', '3', '--project', 'Loja', '20/10/2026')

    assert result.exit_code != 0
    assert 'AAAA-MM-DD' in result.output
