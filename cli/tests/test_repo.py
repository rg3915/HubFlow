import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import CARD, PROJECTS

REPO = {
    'has_token': False,
    'gitlab_project_id': None,
    'create_issues': False,
    'provider': 'github',
    'repository_url': 'https://github.com/acme/loja',
    'has_webhook_secret': False,
    'webhook_path': '/api/webhooks/github/5',
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[]))


def body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_project_repo_configura_token_e_opcoes(run):
    respx.get('http://api.test/api/projects/5/repo').mock(return_value=Response(200, json=REPO))
    route = respx.put('http://api.test/api/projects/5/repo').mock(
        return_value=Response(200, json=REPO | {'has_token': True, 'create_issues': True, 'has_webhook_secret': True})
    )

    result = run('project', 'repo', 'Loja', '--token', 'ghp_x', '--create-issues', '--webhook-secret', 's3')

    assert result.exit_code == 0, result.output
    sent = body(route)
    assert sent['token'] == 'ghp_x' and sent['create_issues'] is True and sent['webhook_secret'] == 's3'
    assert 'webhooks/github/5' in result.output and 'token: sim' in result.output


@respx.mock
def test_project_repo_sem_opcoes_mostra_o_estado(run):
    respx.get('http://api.test/api/projects/5/repo').mock(return_value=Response(200, json=REPO))

    result = run('project', 'repo', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'token: não' in result.output and 'criar issue ao criar card: não' in result.output


@respx.mock
def test_project_repo_check(run):
    respx.post('http://api.test/api/projects/5/repo/check').mock(
        return_value=Response(200, json={'ok': True, 'name': 'acme/loja', 'private': True, 'open_issues': 3})
    )

    result = run('project', 'repo-check', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'acme/loja' in result.output and '3' in result.output


@respx.mock
def test_project_repo_check_falha(run):
    respx.post('http://api.test/api/projects/5/repo/check').mock(
        return_value=Response(400, json={'detail': 'O repositório recusou as credenciais (401).'})
    )

    result = run('project', 'repo-check', 'Loja')

    assert result.exit_code == 1
    assert '401' in result.output


@respx.mock
def test_project_import_issues(run):
    route = respx.post('http://api.test/api/projects/5/import-issues').mock(
        return_value=Response(200, json={'created': 4, 'skipped': 1})
    )

    result = run('project', 'import-issues', 'Loja', '--include-closed')

    assert result.exit_code == 0, result.output
    assert body(route) == {'include_closed': True}
    assert '4' in result.output and '1' in result.output


@respx.mock
def test_card_create_com_issue_mostra_o_numero(run):
    created = CARD | {'issue_number': 42, 'issue_url': 'https://github.com/acme/loja/issues/42'}
    respx.post('http://api.test/api/projects/5/cards').mock(return_value=Response(201, json=created))

    result = run('card', 'create', 'X', '--project', 'Loja', '--no-input')

    assert result.exit_code == 0, result.output
    assert 'Issue #42' in result.output and 'github.com/acme/loja/issues/42' in result.output
