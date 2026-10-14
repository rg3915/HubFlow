import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config

CLIENTS = [{'id': 1, 'name': 'ACME', 'emails': [], 'is_active': True}]
PROJECT = {
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
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/clients').mock(return_value=Response(200, json=CLIENTS))


@respx.mock
def test_project_create_resolve_o_cliente_pelo_nome(run):
    route = respx.post('http://api.test/api/projects').mock(return_value=Response(201, json=PROJECT))

    result = run('project', 'create', 'Loja', '--client', 'ACME', '--provider', 'github', '--repo', 'acme/loja')

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.read())
    assert body == {'client_id': 1, 'name': 'Loja', 'provider': 'github', 'owner': 'acme', 'repo': 'loja', 'emails': []}
    assert 'Loja' in result.output and '#5' in result.output


@respx.mock
def test_project_create_com_cliente_desconhecido_falha(run):
    result = run('project', 'create', 'Loja', '--client', 'Zeta', '--provider', 'github', '--repo', 'acme/loja')

    assert result.exit_code == 1
    assert 'Zeta' in result.output


@respx.mock
def test_project_create_exige_repo_no_formato_owner_repo(run):
    result = run('project', 'create', 'Loja', '--client', 'ACME', '--provider', 'github', '--repo', 'loja')

    assert result.exit_code != 0
    assert 'owner/repo' in result.output


@respx.mock
def test_project_create_rejeita_provedor_desconhecido(run):
    result = run('project', 'create', 'Loja', '--client', 'ACME', '--provider', 'bitbucket', '--repo', 'a/b')

    assert result.exit_code != 0


@respx.mock
def test_project_list_mostra_os_projetos(run):
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=[PROJECT]))

    result = run('project', 'list')

    assert result.exit_code == 0, result.output
    assert 'Loja' in result.output and 'ACME' in result.output and 'github.com/acme/loja' in result.output


@respx.mock
def test_project_list_filtra_por_cliente(run):
    route = respx.get('http://api.test/api/projects', params={'client': '1'}).mock(
        return_value=Response(200, json=[PROJECT])
    )

    result = run('project', 'list', '--client', 'ACME')

    assert result.exit_code == 0, result.output
    assert route.called


@respx.mock
def test_project_list_vazia(run):
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=[]))

    result = run('project', 'list')

    assert 'Nenhum projeto' in result.output
