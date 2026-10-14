import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS

RULE = {
    'id': 7, 'project_id': 5, 'name': 'QA aprovado', 'is_active': True,
    'trigger': 'entered_column', 'trigger_column': 'qa',
    'action': 'move', 'action_column': 'done', 'action_user_id': None, 'action_label_id': None,
    'description': 'Quando o card entrar em QA → mover para Concluído',
}  # fmt: skip


@pytest.fixture(autouse=True)
def api():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    with respx.mock:
        respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
        respx.get('http://api.test/api/projects/5/automations').mock(return_value=Response(200, json=[RULE]))
        yield


def sent(route):
    return json.loads(route.calls.last.request.read())


def test_list(run):
    result = run('automation', 'list', '--project', 'Loja')

    assert result.exit_code == 0, result.output
    assert '#7  ligada  QA aprovado: Quando o card entrar em QA → mover para Concluído' in result.output


@pytest.mark.parametrize(
    ('when', 'then', 'expected'),
    [
        (
            'entered:qa',
            'move:done',
            {'trigger': 'entered_column', 'trigger_column': 'qa', 'action': 'move', 'action_column': 'done'},
        ),
        ('created', 'notify', {'trigger': 'created', 'trigger_column': '', 'action': 'notify', 'action_column': ''}),
        (
            'sla:doing',
            'notify',
            {'trigger': 'sla_breached', 'trigger_column': 'doing', 'action': 'notify', 'action_column': ''},
        ),
    ],
)
def test_add(run, when, then, expected):
    route = respx.post('http://api.test/api/projects/5/automations').mock(return_value=Response(201, json=RULE))

    result = run('automation', 'add', 'Regra', '--project', 'Loja', '--when', when, '--then', then)

    assert result.exit_code == 0, result.output
    assert sent(route).items() >= ({'name': 'Regra'} | expected).items()
    assert 'Automação #7 criada' in result.output


def test_add_responsavel_e_etiqueta_por_nome(run):
    respx.get('http://api.test/api/users').mock(
        return_value=Response(200, json=[{'id': 2, 'email': 'bob@hubflow.com', 'name': 'Bob'}])
    )
    respx.get('http://api.test/api/projects/5/labels').mock(
        return_value=Response(200, json=[{'id': 3, 'name': 'bug'}])
    )
    route = respx.post('http://api.test/api/projects/5/automations').mock(return_value=Response(201, json=RULE))

    run('automation', 'add', 'A', '--project', 'Loja', '--when', 'created', '--then', 'assign:bob@hubflow.com')
    assert sent(route)['action_user_id'] == 2
    run('automation', 'add', 'B', '--project', 'Loja', '--when', 'created', '--then', 'label:BUG')
    assert sent(route)['action_label_id'] == 3


def test_sintaxe_invalida(run):
    result = run('automation', 'add', 'X', '--project', 'Loja', '--when', 'ontem', '--then', 'notify')

    assert result.exit_code == 2 and 'created' in result.output


def test_toggle_e_remove(run):
    put = respx.put('http://api.test/api/automations/7').mock(
        return_value=Response(200, json=RULE | {'is_active': False})
    )
    delete = respx.delete('http://api.test/api/automations/7').mock(return_value=Response(204))

    assert 'desligada' in run('automation', 'toggle', '7', '--project', 'Loja').output
    assert sent(put)['is_active'] is False and sent(put)['action_column'] == 'done'
    assert run('automation', 'remove', '7').exit_code == 0 and delete.called


def test_sla(run):
    sla = {'backlog': None, 'sprint': None, 'doing': 24, 'qa': 48, 'done': None, 'archived': None}
    respx.get('http://api.test/api/projects/5/sla').mock(return_value=Response(200, json=sla))
    put = respx.put('http://api.test/api/projects/5/sla').mock(return_value=Response(200, json=sla))

    shown = run('project', 'sla', 'Loja')
    assert 'QA: 48h' in shown.output and 'Em desenvolvimento: 24h' in shown.output and 'Backlog: —' in shown.output
    run('project', 'sla', 'Loja', '--column', 'qa', '--hours', '48')
    assert sent(put) == {'qa': 48}
    run('project', 'sla', 'Loja', '--column', 'qa', '--clear')
    assert sent(put) == {'qa': None}
