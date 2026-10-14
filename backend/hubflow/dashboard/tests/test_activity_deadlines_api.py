from datetime import date, timedelta

import pytest
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.boards.services import create_card, move_card
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db


def test_atividade_recente_mistura_cards_criados_movidos_e_tempo(api, loja, user):
    a = create_card(loja, user=user, title='A')
    b = create_card(loja, user=user, title='B')
    move_card(a, 'qa', user=user)
    end = timezone.now()
    TimeEntry.objects.create(card=b, user=user, started_at=end - timedelta(minutes=30), ended_at=end)

    data = api.get('/api/dashboard/activity').json()

    kinds = [(item['kind'], item['card_title']) for item in data]
    assert kinds[0] == ('time', 'B')
    assert ('moved', 'A') in kinds and ('created', 'A') in kinds and ('created', 'B') in kinds
    assert data[0]['project_name'] == 'Loja' and data[0]['user']['email'] == 'ana@example.com'
    assert data[0]['data'] == {'hours': 0.5}


def test_atividade_respeita_o_limite(api, loja, user):
    for i in range(30):
        create_card(loja, user=user, title=f'C{i}')

    assert len(api.get('/api/dashboard/activity').json()) == 20
    assert len(api.get('/api/dashboard/activity?limit=5').json()) == 5


def test_prazos_vencidos_e_proximos_7_dias(api, loja):
    today = date.today()
    Card.objects.create(project=loja, title='Atrasado', due_date=today - timedelta(days=2))
    Card.objects.create(project=loja, title='Hoje', due_date=today)
    Card.objects.create(project=loja, title='Em 7', due_date=today + timedelta(days=7))
    Card.objects.create(project=loja, title='Em 8', due_date=today + timedelta(days=8))
    Card.objects.create(project=loja, title='Feito', due_date=today - timedelta(days=1), column='done')
    Card.objects.create(project=loja, title='Sem prazo')

    data = api.get('/api/dashboard/deadlines').json()

    assert [c['title'] for c in data['overdue']] == ['Atrasado']
    assert [c['title'] for c in data['upcoming']] == ['Hoje', 'Em 7']
    assert data['overdue'][0]['project_name'] == 'Loja'


def test_prazos_ignoram_projetos_inativos(api, loja):
    loja.is_active = False
    loja.save()
    Card.objects.create(project=loja, title='Atrasado', due_date=date.today() - timedelta(days=2))

    data = api.get('/api/dashboard/deadlines').json()

    assert data == {'overdue': [], 'upcoming': []}
