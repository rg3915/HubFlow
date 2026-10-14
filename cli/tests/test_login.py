import respx
from httpx import Response

from hubflow_cli.config import load_config


@respx.mock
def test_login_guarda_o_token(run, config_dir):
    route = respx.post('http://api.test/api/auth/login').mock(return_value=Response(200, json={'token': 'abc123'}))

    result = run('login', '--email', 'ana@example.com', '--password', 'segredo123')

    assert result.exit_code == 0, result.output
    assert route.calls.last.request.read() == b'{"email":"ana@example.com","password":"segredo123"}'
    assert load_config()['token'] == 'abc123'
    assert (config_dir / 'config.toml').exists()


@respx.mock
def test_login_pede_email_e_senha_quando_nao_informados(run):
    respx.post('http://api.test/api/auth/login').mock(return_value=Response(200, json={'token': 'abc123'}))

    result = run('login', input='ana@example.com\nsegredo123\n')

    assert result.exit_code == 0, result.output
    assert load_config()['token'] == 'abc123'


@respx.mock
def test_login_com_credenciais_invalidas_falha(run):
    error = Response(401, json={'detail': 'E-mail ou senha inválidos.'})
    respx.post('http://api.test/api/auth/login').mock(return_value=error)

    result = run('login', '--email', 'ana@example.com', '--password', 'errada')

    assert result.exit_code == 1
    assert 'E-mail ou senha inválidos.' in result.output
    assert 'token' not in load_config()


@respx.mock
def test_login_usa_a_url_da_variavel_de_ambiente(run, monkeypatch):
    monkeypatch.setenv('HUBFLOW_URL', 'http://outro.test')
    route = respx.post('http://outro.test/api/auth/login').mock(return_value=Response(200, json={'token': 't'}))

    run('login', '--email', 'ana@example.com', '--password', 'segredo123')

    assert route.called


@respx.mock
def test_login_sem_api_no_ar_mostra_erro_amigavel(run):
    respx.post('http://api.test/api/auth/login').mock(side_effect=ConnectionError)

    result = run('login', '--email', 'ana@example.com', '--password', 'segredo123')

    assert result.exit_code == 1
    assert 'http://api.test' in result.output
