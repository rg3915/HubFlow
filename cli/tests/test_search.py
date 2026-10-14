import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config

EMPTY = {'cards': [], 'projects': [], 'clients': [], 'users': [], 'labels': []}
FOUND = EMPTY | {
    'cards': [
        {
            'id': 9,
            'number': 3,
            'title': 'Corrigir login',
            'column': 'doing',
            'project_id': 5,
            'project_name': 'Loja',
            'client_name': 'ACME',
        }
    ],
    'users': [{'id': 1, 'email': 'ana@example.com', 'name': 'Ana'}],
    'labels': [{'id': 2, 'name': 'login', 'color': '#a33a2e', 'project_id': 5}],
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})


@respx.mock
def test_search_imprime_so_os_grupos_com_resultado(run):
    route = respx.get('http://api.test/api/search').mock(return_value=Response(200, json=FOUND))

    result = run('search', 'login')

    assert result.exit_code == 0, result.output
    assert route.calls.last.request.url.params['q'] == 'login'
    assert 'Cards' in result.output and '#3' in result.output and 'Em desenvolvimento' in result.output
    assert 'Usuários' in result.output and 'ana@example.com' in result.output
    assert 'Etiquetas' in result.output and 'login' in result.output
    assert 'Projetos' not in result.output and 'Clientes' not in result.output


@respx.mock
def test_search_projetos_e_clientes(run):
    found = EMPTY | {
        'projects': [{'id': 5, 'name': 'Loja', 'client_name': 'ACME'}],
        'clients': [{'id': 1, 'name': 'ACME'}],
    }
    respx.get('http://api.test/api/search').mock(return_value=Response(200, json=found))

    result = run('search', 'acme')

    assert result.exit_code == 0, result.output
    assert 'Projetos' in result.output and 'ACME / Loja' in result.output
    assert 'Clientes' in result.output
    assert 'Cards' not in result.output


@respx.mock
def test_search_sem_resultado(run):
    respx.get('http://api.test/api/search').mock(return_value=Response(200, json=EMPTY))

    result = run('search', 'xyz')

    assert result.exit_code == 0, result.output
    assert "Nada encontrado para 'xyz'." in result.output


@respx.mock
def test_search_texto_curto_nem_chama_a_api(run):
    route = respx.get('http://api.test/api/search').mock(return_value=Response(200, json=EMPTY))

    result = run('search', 'a')

    assert result.exit_code != 0
    assert not route.called
    assert '2 caracteres' in result.output
