import respx
from httpx import Response

from hubflow_cli.config import load_config, save_config


@respx.mock
def test_whoami_mostra_o_usuario_logado(run):
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    route = respx.get('http://api.test/api/auth/me').mock(
        return_value=Response(200, json={'id': 1, 'email': 'ana@example.com', 'name': 'Ana'})
    )

    result = run('whoami')

    assert result.exit_code == 0, result.output
    assert 'ana@example.com' in result.output
    assert route.calls.last.request.headers['Authorization'] == 'Bearer abc123'


def test_whoami_sem_login_orienta_a_logar(run):
    result = run('whoami')

    assert result.exit_code == 1
    assert 'hubflow login' in result.output


@respx.mock
def test_whoami_usa_o_token_da_variavel_de_ambiente(run, monkeypatch):
    monkeypatch.setenv('HUBFLOW_TOKEN', 'env-token')
    route = respx.get('http://api.test/api/auth/me').mock(
        return_value=Response(200, json={'id': 1, 'email': 'ana@example.com', 'name': ''})
    )

    run('whoami')

    assert route.calls.last.request.headers['Authorization'] == 'Bearer env-token'


@respx.mock
def test_logout_invalida_o_token_e_apaga_a_configuracao(run, config_dir):
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    route = respx.post('http://api.test/api/auth/logout').mock(return_value=Response(204))

    result = run('logout')

    assert result.exit_code == 0, result.output
    assert route.called
    assert 'token' not in load_config()


@respx.mock
def test_logout_com_token_ja_invalido_limpa_a_configuracao_mesmo_assim(run):
    save_config({'url': 'http://api.test', 'token': 'velho'})
    respx.post('http://api.test/api/auth/logout').mock(return_value=Response(401, json={'detail': 'Unauthorized'}))

    result = run('logout')

    assert result.exit_code == 0, result.output
    assert 'token' not in load_config()


@respx.mock
def test_toda_chamada_se_identifica_como_cli(run, config_dir):
    (config_dir / 'config.toml').write_text('url = "http://api.test"\ntoken = "abc123"\n')
    me = Response(200, json={'email': 'a@b.c', 'name': ''})
    route = respx.get('http://api.test/api/auth/me').mock(return_value=me)

    run('whoami')

    assert route.calls.last.request.headers['X-HubFlow-Client'] == 'cli'
