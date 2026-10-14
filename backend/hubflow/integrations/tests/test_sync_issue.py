import json

import pytest
import respx
from httpx import Response

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
ISSUE = 'https://api.github.com/repos/acme/loja/issues/42'


@pytest.fixture
def linked(loja):
    loja.repo_token = 'ghp_x'
    loja.save()
    return Card.objects.create(
        project=loja, title='Corrigir login', issue_number=42, issue_url='https://github.com/acme/loja/issues/42'
    )


@respx.mock
def test_editar_titulo_e_descricao_atualiza_a_issue(api, linked):
    route = respx.patch(ISSUE).mock(return_value=Response(200, json={}))

    api.put(f'/api/cards/{linked.id}', {'title': 'Login no Safari', 'description': 'iPhone'}, **JSON)

    assert json.loads(route.calls.last.request.read()) == {'title': 'Login no Safari', 'body': 'iPhone'}


@respx.mock
def test_concluir_fecha_a_issue(api, linked):
    route = respx.patch(ISSUE).mock(return_value=Response(200, json={}))

    api.post(f'/api/cards/{linked.id}/move', {'column': 'done'}, **JSON)

    assert json.loads(route.calls.last.request.read()) == {'state': 'closed'}


@respx.mock
def test_arquivar_fecha_a_issue(api, linked):
    route = respx.patch(ISSUE).mock(return_value=Response(200, json={}))

    api.post(f'/api/cards/{linked.id}/archive')

    assert json.loads(route.calls.last.request.read()) == {'state': 'closed'}


@respx.mock
def test_reabrir_quando_volta_de_concluido(api, linked):
    Card.objects.filter(id=linked.id).update(column='done')
    route = respx.patch(ISSUE).mock(return_value=Response(200, json={}))

    api.post(f'/api/cards/{linked.id}/move', {'column': 'qa'}, **JSON)

    assert json.loads(route.calls.last.request.read()) == {'state': 'open'}


@respx.mock
def test_mover_entre_colunas_abertas_nao_chama_o_repositorio(api, linked):
    route = respx.patch(ISSUE)

    api.post(f'/api/cards/{linked.id}/move', {'column': 'qa'}, **JSON)

    assert not route.called


@respx.mock
def test_card_sem_issue_nao_chama_o_repositorio(api, loja):
    loja.repo_token = 'ghp_x'
    loja.save()
    card = Card.objects.create(project=loja, title='Solto')
    route = respx.patch('https://api.github.com/repos/acme/loja/issues/1')

    api.put(f'/api/cards/{card.id}', {'title': 'Outro'}, **JSON)

    assert not route.called


@respx.mock
def test_gitlab_fecha_com_state_event(api, loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id = 'gitlab', 'glpat', 7
    loja.save()
    card = Card.objects.create(project=loja, title='X', issue_number=5, issue_url='u')
    route = respx.put('https://gitlab.com/api/v4/projects/7/issues/5').mock(return_value=Response(200, json={}))

    api.post(f'/api/cards/{card.id}/move', {'column': 'done'}, **JSON)

    assert json.loads(route.calls.last.request.read()) == {'state_event': 'close'}


@respx.mock
def test_falha_remota_nao_impede_a_edicao(api, linked):
    respx.patch(ISSUE).mock(return_value=Response(500, json={}))

    response = api.put(f'/api/cards/{linked.id}', {'title': 'Novo'}, **JSON)

    assert response.status_code == 200
    linked.refresh_from_db()
    assert linked.title == 'Novo'
