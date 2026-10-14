import json

import pytest
import respx
from httpx import Response

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def github(loja):
    loja.repo_token, loja.create_issues = 'ghp_x', True
    loja.save()
    return loja


@respx.mock
def test_cria_issue_no_github_ao_criar_card(api, github):
    route = respx.post('https://api.github.com/repos/acme/loja/issues').mock(
        return_value=Response(201, json={'number': 42, 'html_url': 'https://github.com/acme/loja/issues/42'})
    )

    response = api.post(
        f'/api/projects/{github.id}/cards', {'title': 'Corrigir login', 'description': 'Erro 500'}, **JSON
    )

    assert response.status_code == 201
    data = response.json()
    assert (data['issue_number'], data['issue_url']) == (42, 'https://github.com/acme/loja/issues/42')
    sent = json.loads(route.calls.last.request.read())
    assert sent == {'title': 'Corrigir login', 'body': 'Erro 500'}


@respx.mock
def test_cria_issue_no_gitlab(api, loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id, loja.create_issues = 'gitlab', 'glpat', 7, True
    loja.save()
    route = respx.post('https://gitlab.com/api/v4/projects/7/issues').mock(
        return_value=Response(201, json={'iid': 5, 'web_url': 'https://gitlab.com/acme/loja/-/issues/5'})
    )

    data = api.post(f'/api/projects/{loja.id}/cards', {'title': 'X'}, **JSON).json()

    assert (data['issue_number'], data['issue_url']) == (5, 'https://gitlab.com/acme/loja/-/issues/5')
    assert json.loads(route.calls.last.request.read()) == {'title': 'X', 'description': ''}


@respx.mock
def test_opcao_desligada_nao_chama_o_repositorio(api, loja):
    loja.repo_token = 'ghp_x'
    loja.save()
    route = respx.post('https://api.github.com/repos/acme/loja/issues')

    data = api.post(f'/api/projects/{loja.id}/cards', {'title': 'X'}, **JSON).json()

    assert not route.called
    assert data['issue_number'] is None


@respx.mock
def test_falha_no_repositorio_nao_impede_o_card(api, github):
    respx.post('https://api.github.com/repos/acme/loja/issues').mock(return_value=Response(401, json={}))

    response = api.post(f'/api/projects/{github.id}/cards', {'title': 'X'}, **JSON)

    assert response.status_code == 201
    assert response.json()['issue_number'] is None
    assert Card.objects.filter(title='X').exists()


@respx.mock
def test_titulo_do_card_leva_o_numero_da_issue_para_o_quadro(api, github):
    respx.post('https://api.github.com/repos/acme/loja/issues').mock(
        return_value=Response(201, json={'number': 42, 'html_url': 'https://github.com/acme/loja/issues/42'})
    )
    api.post(f'/api/projects/{github.id}/cards', {'title': 'X'}, **JSON)

    board_card = api.get(f'/api/projects/{github.id}/board').json()['columns'][0]['cards'][0]

    assert board_card['issue_number'] == 42
