from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db


def test_meus_cards_em_aberto_com_vencidos_primeiro(api, loja, user):
    today = timezone.localdate()
    other = get_user_model().objects.create_user(email='bob@hubflow.com', password='x')
    later = Card.objects.create(project=loja, title='Depois', assignee=user, due_date=today + timedelta(days=3))
    no_due = Card.objects.create(project=loja, title='Sem prazo', assignee=user, column='doing')
    overdue = Card.objects.create(project=loja, title='Atrasado', assignee=user, due_date=today - timedelta(days=1))
    Card.objects.create(project=loja, title='Feito', assignee=user, column='done')
    Card.objects.create(project=loja, title='Arquivado', assignee=user, column='archived')
    Card.objects.create(project=loja, title='Do Bob', assignee=other)

    data = api.get('/api/me/cards').json()

    assert [c['id'] for c in data] == [overdue.id, later.id, no_due.id]
    assert data[0]['is_overdue'] is True
    assert data[0]['project_name'] == 'Loja' and data[0]['client_name'] == 'ACME' and data[0]['column'] == 'backlog'


def test_sem_cards(api):
    assert api.get('/api/me/cards').json() == []
