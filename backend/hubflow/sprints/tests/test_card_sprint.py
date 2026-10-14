import pytest

from hubflow.boards.models import Card
from hubflow.boards.services import create_card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def test_sem_sprint_no_projeto_cria_a_sprint_1(loja):
    # RN-61
    card = create_card(loja, title='Primeiro')

    assert card.sprint.number == 1
    assert Sprint.objects.filter(project=loja).count() == 1


def test_sem_sprint_informada_usa_a_ultima_aberta(loja):
    Sprint.objects.create(project=loja).close()
    second = Sprint.objects.create(project=loja)

    card = create_card(loja, title='Novo')

    assert card.sprint == second


def test_todas_fechadas_cria_uma_nova(loja):
    Sprint.objects.create(project=loja).close()

    card = create_card(loja, title='Novo')

    assert card.sprint.number == 2
    assert card.sprint.is_open


def test_sprint_informada_e_usada(loja):
    first = Sprint.objects.create(project=loja)
    Sprint.objects.create(project=loja)

    card = create_card(loja, title='Novo', sprint=first)

    assert card.sprint == first


def test_api_cria_card_com_sprint_informada(api, loja):
    sprint = Sprint.objects.create(project=loja)

    response = api.post(f'/api/projects/{loja.id}/cards', {'title': 'X', 'sprint_id': sprint.id}, **JSON)

    assert response.status_code == 201
    assert response.json()['sprint'] == {'id': sprint.id, 'number': 1, 'name': ''}


def test_api_sprint_de_outro_projeto_retorna_400(api, loja):
    other = Project.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    foreign = Sprint.objects.create(project=other)

    response = api.post(f'/api/projects/{loja.id}/cards', {'title': 'X', 'sprint_id': foreign.id}, **JSON)

    assert response.status_code == 400


def test_api_muda_a_sprint_do_card(api, loja):
    card = create_card(loja, title='X')
    second = Sprint.objects.create(project=loja)

    response = api.put(f'/api/cards/{card.id}', {'title': 'X', 'sprint_id': second.id}, **JSON)

    assert response.json()['sprint']['number'] == 2


def test_quadro_filtra_por_sprint(api, loja):
    first = create_card(loja, title='Da 1').sprint
    second = Sprint.objects.create(project=loja)
    create_card(loja, title='Da 2', sprint=second)

    board = api.get(f'/api/projects/{loja.id}/board?sprint={second.id}').json()
    all_cards = api.get(f'/api/projects/{loja.id}/board').json()

    assert [c['title'] for c in board['columns'][0]['cards']] == ['Da 2']
    assert len(all_cards['columns'][0]['cards']) == 2
    assert Card.objects.filter(sprint=first).count() == 1
