import hashlib
import hmac
import json

import pytest
from django.test import Client as HttpClient

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

SECRET = 'segredo-webhook'


@pytest.fixture
def github(loja):
    loja.repo_token, loja.webhook_secret = 'ghp_x', SECRET
    loja.save()
    return loja


@pytest.fixture
def linked(github):
    return Card.objects.create(project=github, title='Login', issue_number=42, column='doing')


def github_push(project, message, secret=SECRET):
    body = json.dumps({'ref': 'refs/heads/main', 'commits': [{'id': 'abc', 'message': message}]}).encode()
    signature = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return HttpClient().post(
        f'/api/webhooks/github/{project.id}',
        body,
        content_type='application/json',
        headers={'X-GitHub-Event': 'push', 'X-Hub-Signature-256': signature},
    )


def test_commit_com_close_move_o_card_para_concluido(github, linked):
    response = github_push(github, 'Corrige login. close #42')

    assert response.status_code == 200
    assert response.json() == {'moved': [42]}
    linked.refresh_from_db()
    assert linked.column == 'done'


def test_fixes_e_resolves_tambem_fecham(github, linked):
    github_push(github, 'Fixes #42')
    linked.refresh_from_db()
    assert linked.column == 'done'


def test_assinatura_invalida_retorna_403(github, linked):
    response = github_push(github, 'close #42', secret='errado')

    assert response.status_code == 403
    linked.refresh_from_db()
    assert linked.column == 'doing'


def test_numero_desconhecido_e_ignorado(github, linked):
    assert github_push(github, 'close #999').json() == {'moved': []}


def test_pull_request_mesclado_fecha_o_card(github, linked):
    body = json.dumps(
        {'action': 'closed', 'pull_request': {'merged': True, 'title': 'Login', 'body': 'Fixes #42'}}
    ).encode()
    signature = 'sha256=' + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

    response = HttpClient().post(
        f'/api/webhooks/github/{github.id}',
        body,
        content_type='application/json',
        headers={'X-GitHub-Event': 'pull_request', 'X-Hub-Signature-256': signature},
    )

    assert response.json() == {'moved': [42]}


def test_gitlab_usa_o_token_do_cabecalho(loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id, loja.webhook_secret = 'gitlab', 'glpat', 7, SECRET
    loja.save()
    card = Card.objects.create(project=loja, title='X', issue_number=5)
    body = {'object_kind': 'push', 'commits': [{'message': 'Resolve #5'}]}

    response = HttpClient().post(
        f'/api/webhooks/gitlab/{loja.id}', body, content_type='application/json', headers={'X-Gitlab-Token': SECRET}
    )

    assert response.status_code == 200
    card.refresh_from_db()
    assert card.column == 'done'


def test_webhook_nao_exige_login_mas_exige_segredo_configurado(loja, linked):
    loja.webhook_secret = ''
    loja.save()

    assert github_push(loja, 'close #42').status_code == 403
