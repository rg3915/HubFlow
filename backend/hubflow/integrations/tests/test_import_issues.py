import pytest
import respx
from httpx import Response

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
ISSUES_URL = 'https://api.github.com/repos/acme/loja/issues'


def gh_issue(number, title, state='open', body='', pull=False):
    data = {
        'number': number,
        'title': title,
        'state': state,
        'body': body,
        'html_url': f'https://github.com/acme/loja/issues/{number}',
    }
    if pull:
        data['pull_request'] = {'url': 'x'}
    return data


@pytest.fixture
def github(loja):
    loja.repo_token = 'ghp_x'
    loja.save()
    return loja


@respx.mock
def test_importa_issues_abertas_como_cards_no_backlog(api, github):
    respx.get(ISSUES_URL).mock(
        return_value=Response(200, json=[gh_issue(1, 'Login'), gh_issue(2, 'Pix', body='Integrar')])
    )

    response = api.post(f'/api/projects/{github.id}/import-issues', {}, **JSON)

    assert response.status_code == 200
    assert response.json() == {'created': 2, 'skipped': 0}
    cards = list(Card.objects.filter(project=github).order_by('issue_number'))
    assert [(c.issue_number, c.title, c.description, c.column) for c in cards] == [
        (1, 'Login', '', 'backlog'),
        (2, 'Pix', 'Integrar', 'backlog'),
    ]
    assert cards[0].issue_url == 'https://github.com/acme/loja/issues/1'


@respx.mock
def test_nao_duplica_issues_ja_importadas(api, github):
    Card.objects.create(project=github, title='Login', issue_number=1)
    respx.get(ISSUES_URL).mock(return_value=Response(200, json=[gh_issue(1, 'Login'), gh_issue(3, 'Nova')]))

    data = api.post(f'/api/projects/{github.id}/import-issues', {}, **JSON).json()

    assert data == {'created': 1, 'skipped': 1}


@respx.mock
def test_pull_requests_sao_ignorados(api, github):
    respx.get(ISSUES_URL).mock(return_value=Response(200, json=[gh_issue(9, 'PR', pull=True)]))

    data = api.post(f'/api/projects/{github.id}/import-issues', {}, **JSON).json()

    assert data == {'created': 0, 'skipped': 1}


@respx.mock
def test_issues_fechadas_so_com_opcao_e_vao_para_concluido(api, github):
    route = respx.get(ISSUES_URL).mock(return_value=Response(200, json=[gh_issue(4, 'Feita', state='closed')]))

    api.post(f'/api/projects/{github.id}/import-issues', {'include_closed': True}, **JSON)

    assert route.calls.last.request.url.params['state'] == 'all'
    assert Card.objects.get(issue_number=4).column == 'done'


@respx.mock
def test_importa_do_gitlab(api, loja):
    loja.provider, loja.repo_token, loja.gitlab_project_id = 'gitlab', 'glpat', 7
    loja.save()
    respx.get('https://gitlab.com/api/v4/projects/7/issues').mock(
        return_value=Response(
            200, json=[{'iid': 11, 'title': 'GL', 'state': 'opened', 'description': 'd', 'web_url': 'u'}]
        )
    )

    data = api.post(f'/api/projects/{loja.id}/import-issues', {}, **JSON).json()

    assert data['created'] == 1
    assert Card.objects.get(issue_number=11).issue_url == 'u'


def test_sem_token_retorna_400(api, loja):
    assert api.post(f'/api/projects/{loja.id}/import-issues', {}, **JSON).status_code == 400
