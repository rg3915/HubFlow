import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})


def person(**overrides):
    return {
        'id': 5,
        'email': 'dev@hubflow.com',
        'name': 'Dev Silva',
        'first_name': 'Dev',
        'avatar_url': None,
        'is_active': True,
        'is_superuser': False,
        'roles': ['Desenvolvedor'],
        'permissions': ['boards.add_card', 'permissions.use_cli'],
        'extra_permissions': [],
        'clients': [{'id': 1, 'name': 'ACME'}],
    } | overrides


def mock_people(*people):
    return respx.get('http://api.test/api/users/manage').mock(return_value=Response(200, json=list(people)))


@respx.mock
def test_user_list(run):
    mock_people(person(), person(id=6, email='ex@hubflow.com', name='', roles=[], clients=[], is_active=False))

    result = run('user', 'list')

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert all(text in lines[0] for text in ('dev@hubflow.com', 'Dev Silva', 'Desenvolvedor', 'ACME'))
    assert 'ex@hubflow.com' in lines[1] and 'inativo' in lines[1]


@respx.mock
def test_user_invite_com_papel_e_cliente(run):
    respx.get('http://api.test/api/clients').mock(return_value=Response(200, json=[{'id': 1, 'name': 'ACME'}]))
    route = respx.post('http://api.test/api/users/invite').mock(return_value=Response(201, json=person()))

    options = ['--name', 'Dev Silva', '--role', 'Desenvolvedor', '--client', 'acme']
    result = run('user', 'invite', 'dev@hubflow.com', *options)

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {
        'email': 'dev@hubflow.com',
        'name': 'Dev Silva',
        'roles': ['Desenvolvedor'],
        'client_ids': [1],
    }
    assert 'Convite enviado para dev@hubflow.com.' in result.output


@respx.mock
def test_user_invite_repetido_mostra_o_erro(run):
    error = Response(400, json={'detail': 'Já existe uma pessoa com este e-mail.'})
    respx.post('http://api.test/api/users/invite').mock(return_value=error)

    result = run('user', 'invite', 'dev@hubflow.com')

    assert result.exit_code == 1
    assert 'Já existe uma pessoa com este e-mail.' in result.output


@respx.mock
def test_user_role_define_os_papeis(run):
    mock_people(person())
    route = respx.put('http://api.test/api/users/5/roles').mock(
        return_value=Response(200, json=person(roles=['Financeiro', 'Gerente']))
    )

    result = run('user', 'role', 'DEV@hubflow.com', '--set', 'Gerente', '--set', 'Financeiro')

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.read()) == {'roles': ['Gerente', 'Financeiro']}
    assert 'Financeiro, Gerente' in result.output


@respx.mock
def test_user_grant_adiciona_e_revoke_remove(run):
    mock_people(person(extra_permissions=['billing.view_payment']))
    route = respx.put('http://api.test/api/users/5/permissions').mock(return_value=Response(200, json=person()))

    run('user', 'grant', 'dev@hubflow.com', '--perm', 'permissions.view_own_payments')
    assert json.loads(route.calls.last.request.read()) == {
        'permissions': ['billing.view_payment', 'permissions.view_own_payments']
    }

    run('user', 'grant', 'dev@hubflow.com', '--perm', 'billing.view_payment', '--revoke')
    assert json.loads(route.calls.last.request.read()) == {'permissions': []}


@respx.mock
def test_pessoa_desconhecida_da_dica(run):
    mock_people(person())

    result = run('user', 'role', 'nao@hubflow.com', '--set', 'Gerente')

    assert result.exit_code == 1
    assert 'hubflow user list' in result.output


@respx.mock
def test_sem_permissao_mostra_o_motivo(run):
    error = Response(403, json={'detail': 'Você não tem permissão para isto (Gerenciar papéis e permissões).'})
    respx.get('http://api.test/api/users/manage').mock(return_value=error)

    result = run('user', 'list')

    assert result.exit_code == 1
    assert 'Gerenciar papéis e permissões' in result.output
