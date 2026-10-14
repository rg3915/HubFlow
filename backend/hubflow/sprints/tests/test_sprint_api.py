import pytest

from hubflow.boards.services import create_card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Milestone, Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def test_cria_sprint(api, loja):
    response = api.post(f'/api/projects/{loja.id}/sprints', {'name': 'Checkout', 'start_date': '2026-10-13'}, **JSON)

    assert response.status_code == 201
    data = response.json()
    assert (data['number'], data['name'], data['start_date'], data['is_open']) == (1, 'Checkout', '2026-10-13', True)


def test_cria_sprint_sem_nada(api, loja):
    response = api.post(f'/api/projects/{loja.id}/sprints', {}, **JSON)

    assert response.status_code == 201
    assert response.json()['number'] == 1


def test_sprint_com_milestone(api, loja):
    milestone = Milestone.objects.create(project=loja, title='v1')

    response = api.post(f'/api/projects/{loja.id}/sprints', {'milestone_id': milestone.id}, **JSON)

    assert response.json()['milestone']['title'] == 'v1'


def test_milestone_de_outro_projeto_retorna_400(api, loja):
    other = Project.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    foreign = Milestone.objects.create(project=other, title='x')

    response = api.post(f'/api/projects/{loja.id}/sprints', {'milestone_id': foreign.id}, **JSON)

    assert response.status_code == 400


def test_fim_antes_do_inicio_retorna_400(api, loja):
    data = {'start_date': '2026-10-20', 'end_date': '2026-10-10'}

    assert api.post(f'/api/projects/{loja.id}/sprints', data, **JSON).status_code == 400


def test_lista_sprints_da_mais_recente_para_a_mais_antiga_com_contagem(api, loja):
    first = Sprint.objects.create(project=loja)
    create_card(loja, title='A', sprint=first)
    create_card(loja, title='B', sprint=first)
    Sprint.objects.create(project=loja)

    response = api.get(f'/api/projects/{loja.id}/sprints')

    assert [s['number'] for s in response.json()] == [2, 1]
    assert response.json()[1]['cards_count'] == 2


def test_sprint_atual(api, loja):
    Sprint.objects.create(project=loja).close()
    current = Sprint.objects.create(project=loja)

    response = api.get(f'/api/projects/{loja.id}/sprints/current')

    assert response.json()['id'] == current.id


def test_sem_sprint_aberta_retorna_404(api, loja):
    assert api.get(f'/api/projects/{loja.id}/sprints/current').status_code == 404


def test_edita_sprint(api, loja):
    sprint = Sprint.objects.create(project=loja)

    response = api.put(f'/api/sprints/{sprint.id}', {'name': 'Nova', 'end_date': '2026-10-30'}, **JSON)

    assert response.status_code == 200
    sprint.refresh_from_db()
    assert (sprint.name, str(sprint.end_date)) == ('Nova', '2026-10-30')


def test_fecha_sprint_sem_mexer_nos_cards(api, loja):
    # RN-62
    sprint = Sprint.objects.create(project=loja)
    card = create_card(loja, title='A', sprint=sprint)

    response = api.post(f'/api/sprints/{sprint.id}/close')

    assert response.status_code == 200
    assert response.json()['is_open'] is False
    card.refresh_from_db()
    assert (card.sprint, card.column) == (sprint, 'backlog')


def test_nao_exclui_sprint_com_cards(api, loja):
    sprint = create_card(loja, title='A').sprint

    assert api.delete(f'/api/sprints/{sprint.id}').status_code == 400


def test_exclui_sprint_vazia(api, loja):
    sprint = Sprint.objects.create(project=loja)

    assert api.delete(f'/api/sprints/{sprint.id}').status_code == 204
