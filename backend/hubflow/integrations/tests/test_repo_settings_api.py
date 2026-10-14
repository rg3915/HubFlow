import pytest
import respx
from httpx import Response

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def test_projeto_guarda_token_e_id_do_gitlab_sem_devolver_o_token(api, loja):
    body = {'token': 'ghp_segredo', 'gitlab_project_id': None, 'create_issues': True}

    response = api.put(f'/api/projects/{loja.id}/repo', body, **JSON)

    assert response.status_code == 200
    data = response.json()
    assert data['has_token'] is True and 'token' not in data and 'ghp_segredo' not in response.content.decode()
    assert data['create_issues'] is True
    loja.refresh_from_db()
    assert loja.repo_token == 'ghp_segredo'


def test_projeto_na_api_nao_expoe_o_token(api, loja):
    loja.repo_token = 'ghp_segredo'
    loja.save()

    text = api.get(f'/api/projects/{loja.id}').content.decode()

    assert 'ghp_segredo' not in text and '"has_token": true' in text


def test_limpa_o_token(api, loja):
    loja.repo_token = 'ghp_segredo'
    loja.save()

    response = api.put(f'/api/projects/{loja.id}/repo', {'token': '', 'create_issues': False}, **JSON)

    assert response.json()['has_token'] is False
    loja.refresh_from_db()
    assert loja.repo_token == ''


def test_gitlab_guarda_o_id_numerico(api, loja):
    loja.provider = 'gitlab'
    loja.save()

    response = api.put(f'/api/projects/{loja.id}/repo', {'token': 'glpat-x', 'gitlab_project_id': 4242}, **JSON)

    assert response.json()['gitlab_project_id'] == 4242


@respx.mock
def test_check_github_ok(api, loja):
    loja.repo_token = 'ghp_segredo'
    loja.save()
    route = respx.get('https://api.github.com/repos/acme/loja').mock(
        return_value=Response(200, json={'full_name': 'acme/loja', 'private': True, 'open_issues_count': 3})
    )

    response = api.post(f'/api/projects/{loja.id}/repo/check')

    assert response.status_code == 200
    assert response.json() == {'ok': True, 'name': 'acme/loja', 'private': True, 'open_issues': 3}
    assert route.calls.last.request.headers['Authorization'] == 'Bearer ghp_segredo'


@respx.mock
def test_check_gitlab_ok(api, loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id = 'gitlab', 'glpat-x', 4242
    loja.save()
    route = respx.get('https://gitlab.com/api/v4/projects/4242').mock(
        return_value=Response(
            200, json={'path_with_namespace': 'acme/loja', 'visibility': 'private', 'open_issues_count': 1}
        )
    )

    response = api.post(f'/api/projects/{loja.id}/repo/check')

    assert response.json() == {'ok': True, 'name': 'acme/loja', 'private': True, 'open_issues': 1}
    assert route.calls.last.request.headers['PRIVATE-TOKEN'] == 'glpat-x'


@respx.mock
def test_check_com_token_invalido(api, loja):
    loja.repo_token = 'ruim'
    loja.save()
    respx.get('https://api.github.com/repos/acme/loja').mock(
        return_value=Response(401, json={'message': 'Bad credentials'})
    )

    response = api.post(f'/api/projects/{loja.id}/repo/check')

    assert response.status_code == 400
    assert 'credenciais' in response.json()['detail'].lower() or '401' in response.json()['detail']


def test_check_sem_token(api, loja):
    response = api.post(f'/api/projects/{loja.id}/repo/check')

    assert response.status_code == 400
    assert 'token' in response.json()['detail'].lower()
