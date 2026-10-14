import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})


@respx.mock
def test_client_create_cria_o_cliente(run):
    route = respx.post('http://api.test/api/clients').mock(
        return_value=Response(201, json={'id': 7, 'name': 'ACME', 'emails': [], 'is_active': True})
    )

    result = run('client', 'create', 'ACME')

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {'name': 'ACME', 'emails': []}
    assert 'ACME' in result.output and '#7' in result.output


@respx.mock
def test_client_create_aceita_emails(run):
    created = {'id': 7, 'name': 'ACME', 'emails': ['a@acme.com', 'b@acme.com'], 'is_active': True}
    route = respx.post('http://api.test/api/clients').mock(return_value=Response(201, json=created))

    run('client', 'create', 'ACME', '--emails', 'a@acme.com,b@acme.com')

    assert json.loads(route.calls.last.request.read())['emails'] == ['a@acme.com', 'b@acme.com']


@respx.mock
def test_client_create_com_nome_repetido_mostra_o_erro(run):
    respx.post('http://api.test/api/clients').mock(
        return_value=Response(400, json={'detail': 'Já existe um cliente com este nome.'})
    )

    result = run('client', 'create', 'ACME')

    assert result.exit_code == 1
    assert 'Já existe um cliente com este nome.' in result.output


@respx.mock
def test_client_list_mostra_os_clientes(run):
    respx.get('http://api.test/api/clients').mock(
        return_value=Response(
            200,
            json=[
                {'id': 1, 'name': 'ACME', 'emails': ['ti@acme.com'], 'is_active': True},
                {'id': 2, 'name': 'Beta', 'emails': [], 'is_active': False},
            ],
        )
    )

    result = run('client', 'list')

    assert result.exit_code == 0, result.output
    assert 'ACME' in result.output and 'ti@acme.com' in result.output
    assert 'Beta' in result.output and 'inativo' in result.output


@respx.mock
def test_client_list_vazia(run):
    respx.get('http://api.test/api/clients').mock(return_value=Response(200, json=[]))

    result = run('client', 'list')

    assert result.exit_code == 0
    assert 'Nenhum cliente' in result.output


def test_client_exige_login(run, config_dir):
    (config_dir / 'config.toml').unlink()

    result = run('client', 'list')

    assert result.exit_code == 1
    assert 'hubflow login' in result.output
