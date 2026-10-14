from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def world(loja, user):
    beta = Client.objects.create(name='Beta')
    site = Project.objects.create(client=beta, name='Site', provider='github', owner='b', repo='s')
    dead = Project.objects.create(client=beta, name='Antigo', provider='github', owner='b', repo='a', is_active=False)
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123', name='Bob')
    cards = {
        'a': Card.objects.create(project=loja, title='A', column='doing', assignee=user),
        'b': Card.objects.create(project=loja, title='B', column='backlog'),
        'c': Card.objects.create(project=site, title='C', column='doing', assignee=bob),
        'd': Card.objects.create(project=site, title='D', column='done'),
        'x': Card.objects.create(project=dead, title='X', column='doing'),
    }
    TimeEntry.objects.create(card=cards['a'], user=user, started_at=timezone.now() - timedelta(minutes=30))
    TimeEntry.objects.create(card=cards['c'], user=bob, started_at=timezone.now() - timedelta(minutes=5))
    return cards


def test_cards_por_coluna_dos_projetos_ativos(api, world):
    data = api.get('/api/dashboard').json()

    assert data['by_column'] == [
        {'key': 'backlog', 'label': 'Backlog', 'count': 1},
        {'key': 'sprint', 'label': 'Sprint', 'count': 0},
        {'key': 'doing', 'label': 'Em desenvolvimento', 'count': 2},
        {'key': 'qa', 'label': 'QA', 'count': 0},
        {'key': 'done', 'label': 'Concluído', 'count': 1},
        {'key': 'archived', 'label': 'Arquivadas', 'count': 0},
    ]


def test_em_desenvolvimento_agora_com_projeto_e_responsavel(api, world):
    data = api.get('/api/dashboard').json()

    doing = data['in_progress']
    assert [c['title'] for c in doing] == ['A', 'C']
    assert doing[0]['project_name'] == 'Loja' and doing[0]['client_name'] == 'ACME'
    assert doing[0]['assignee']['email'] == 'ana@example.com'
    assert doing[0]['time']['running'] is True


def test_cronometros_abertos(api, world):
    data = api.get('/api/dashboard').json()

    running = data['running_timers']
    assert [(r['card_title'], r['user']['email']) for r in running] == [
        ('A', 'ana@example.com'),
        ('C', 'bob@hubflow.com'),
    ]
    assert running[0]['started_at'] is not None
    assert running[0]['mine'] is True and running[1]['mine'] is False


def test_totais(api, world):
    data = api.get('/api/dashboard').json()

    assert data['totals'] == {'clients': 2, 'projects': 2, 'open_cards': 3, 'running_timers': 2}


def test_vazio(api):
    data = api.get('/api/dashboard').json()

    assert data['totals'] == {'clients': 0, 'projects': 0, 'open_cards': 0, 'running_timers': 0}
    assert data['in_progress'] == [] and data['running_timers'] == []
