import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS

PROJECT = PROJECTS[0] | {'notify_on_created': True, 'notify_on_moved': True, 'notify_on_done': True}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=[PROJECT]))


def sent_body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_notify_desliga_eventos(run):
    route = respx.put('http://api.test/api/projects/5').mock(
        return_value=Response(200, json=PROJECT | {'notify_on_moved': False, 'notify_on_done': False})
    )

    result = run('project', 'notify', 'Loja', '--off', 'moved,done')

    assert result.exit_code == 0, result.output
    body = sent_body(route)
    assert (body['notify_on_created'], body['notify_on_moved'], body['notify_on_done']) == (True, False, False)
    assert body['client_id'] == 1 and body['repo'] == 'loja'
    assert 'criado' in result.output and 'movido' in result.output


@respx.mock
def test_notify_liga_eventos(run):
    current = [PROJECT | {'notify_on_done': False}]
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=current))
    route = respx.put('http://api.test/api/projects/5').mock(return_value=Response(200, json=PROJECT))

    run('project', 'notify', 'Loja', '--on', 'done')

    assert sent_body(route)['notify_on_done'] is True


@respx.mock
def test_notify_rejeita_evento_desconhecido(run):
    result = run('project', 'notify', 'Loja', '--on', 'explodiu')

    assert result.exit_code != 0
    assert 'created, moved, done' in result.output


@respx.mock
def test_notify_sem_opcoes_mostra_o_estado(run):
    result = run('project', 'notify', 'Loja')

    assert result.exit_code == 0, result.output
    assert 'criado' in result.output


@respx.mock
def test_emails_define_os_destinatarios(run):
    route = respx.put('http://api.test/api/projects/5').mock(
        return_value=Response(200, json=PROJECT | {'emails': ['a@acme.com', 'b@acme.com']})
    )

    result = run('project', 'emails', 'Loja', '--set', 'a@acme.com, b@acme.com')

    assert result.exit_code == 0, result.output
    assert sent_body(route)['emails'] == ['a@acme.com', 'b@acme.com']
    assert 'a@acme.com' in result.output


@respx.mock
def test_emails_vazio_volta_a_usar_os_do_cliente(run):
    route = respx.put('http://api.test/api/projects/5').mock(return_value=Response(200, json=PROJECT))

    result = run('project', 'emails', 'Loja', '--set', '')

    assert sent_body(route)['emails'] == []
    assert 'cliente' in result.output
