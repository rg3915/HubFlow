from datetime import date

import pytest

from hubflow.billing.models import Payment
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db


@pytest.fixture
def payments(loja):
    beta = Client.objects.create(name='Beta')
    site = Project.objects.create(client=beta, name='Site', provider='github', owner='b', repo='s')
    s1, s2 = Sprint.objects.create(project=loja), Sprint.objects.create(project=site)
    a = Payment.objects.create(sprint=s1, hourly_rate=100, fixed_value=1000, issue_date=date(2026, 9, 10))
    b = Payment.objects.create(sprint=s1, hourly_rate=100, fixed_value=500, issue_date=date(2026, 10, 1))
    c = Payment.objects.create(sprint=s2, hourly_rate=100, fixed_value=2000, issue_date=date(2026, 10, 5))
    d = Payment.objects.create(sprint=s2, hourly_rate=100, fixed_value=300, issue_date=date(2025, 12, 1))
    for paid in (a, c):
        paid.status, paid.payment_date = 'paid', paid.issue_date
        paid.save()
    return {'a': a, 'b': b, 'c': c, 'd': d}


def test_totais_recebido_e_pendente(api, payments):
    data = api.get('/api/payments/summary').json()

    assert data['received'] == '3000.00'
    assert data['pending'] == '800.00'


def test_por_cliente(api, payments):
    data = api.get('/api/payments/summary').json()

    assert data['by_client'] == [
        {'client_id': payments['c'].client.id, 'client_name': 'Beta', 'received': '2000.00', 'pending': '300.00'},
        {'client_id': payments['a'].client.id, 'client_name': 'ACME', 'received': '1000.00', 'pending': '500.00'},
    ]


def test_por_mes_do_ano(api, payments):
    data = api.get('/api/payments/summary?year=2026').json()

    assert data['by_month'] == [
        {'month': '2026-09', 'received': '1000.00', 'pending': '0.00'},
        {'month': '2026-10', 'received': '2000.00', 'pending': '500.00'},
    ]
    assert data['received'] == '3000.00' and data['pending'] == '500.00'


def test_anos_disponiveis(api, payments):
    assert api.get('/api/payments/summary').json()['years'] == [2026, 2025]


def test_filtro_por_cliente(api, payments):
    data = api.get(f'/api/payments/summary?client={payments["a"].client.id}').json()

    assert (data['received'], data['pending']) == ('1000.00', '500.00')


def test_sem_pagamentos(api):
    data = api.get('/api/payments/summary').json()

    assert data == {'received': '0.00', 'pending': '0.00', 'by_client': [], 'by_month': [], 'years': []}


def test_resumo_bate_com_o_valor_total_do_pagamento(api, loja, user):
    from datetime import timedelta

    from django.utils import timezone

    from hubflow.boards.models import Card
    from hubflow.timetracking.models import TimeEntry

    sprint = Sprint.objects.create(project=loja)
    card = Card.objects.create(project=loja, title='A', sprint=sprint)
    start = timezone.now() - timedelta(hours=3)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=2, seconds=9))
    payment = Payment.objects.create(sprint=sprint, hourly_rate=150, issue_date=date(2026, 10, 14))

    summary = api.get('/api/payments/summary').json()

    assert summary['pending'] == str(payment.total_value)
