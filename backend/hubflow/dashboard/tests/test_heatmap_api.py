from datetime import timedelta

import pytest
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db


def spend_on(card, user, day, hours):
    start = timezone.make_aware(timezone.datetime(day.year, day.month, day.day, 9, 0))
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=hours))


def test_heatmap_26_semanas_com_niveis(api, loja, user):
    card = Card.objects.create(project=loja, title='A')
    today = timezone.localdate()
    spend_on(card, user, today, 0.5)
    spend_on(card, user, today - timedelta(days=1), 2)
    spend_on(card, user, today - timedelta(days=2), 4)
    spend_on(card, user, today - timedelta(days=3), 6)
    spend_on(card, user, today - timedelta(weeks=30), 8)  # fora da janela

    data = api.get('/api/dashboard/heatmap').json()

    days = {d['date']: d for d in data['days']}
    assert data['weeks'] == 26
    assert len(data['days']) == 26 * 7
    assert days[today.isoformat()] == {'date': today.isoformat(), 'hours': 0.5, 'level': 1}
    assert days[(today - timedelta(days=1)).isoformat()]['level'] == 2
    assert days[(today - timedelta(days=2)).isoformat()]['level'] == 3
    assert days[(today - timedelta(days=3)).isoformat()]['level'] == 4
    assert days[(today - timedelta(days=10)).isoformat()] == {
        'date': (today - timedelta(days=10)).isoformat(),
        'hours': 0.0,
        'level': 0,
    }
    assert data['total_hours'] == 12.5


def test_heatmap_filtra_por_projeto(api, loja, user):
    other = Project.objects.create(client=loja.client, name='App', provider='github', owner='a', repo='p')
    spend_on(Card.objects.create(project=loja, title='A'), user, timezone.localdate(), 1)
    spend_on(Card.objects.create(project=other, title='B'), user, timezone.localdate(), 2)

    data = api.get(f'/api/dashboard/heatmap?project={loja.id}').json()

    assert data['total_hours'] == 1.0


def test_horas_da_semana_por_projeto(api, loja, user):
    beta = Client.objects.create(name='Beta')
    site = Project.objects.create(client=beta, name='Site', provider='github', owner='b', repo='s')
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    spend_on(Card.objects.create(project=loja, title='A'), user, monday, 3)
    spend_on(Card.objects.create(project=loja, title='B'), user, today, 1)
    spend_on(Card.objects.create(project=site, title='C'), user, today, 2.5)
    spend_on(Card.objects.create(project=site, title='D'), user, monday - timedelta(days=1), 9)  # semana passada

    data = api.get('/api/dashboard/week').json()

    assert data['start'] == monday.isoformat()
    assert data['total_hours'] == 6.5
    assert data['by_project'] == [
        {'project_id': loja.id, 'project_name': 'Loja', 'client_name': 'ACME', 'hours': 4.0},
        {'project_id': site.id, 'project_name': 'Site', 'client_name': 'Beta', 'hours': 2.5},
    ]
