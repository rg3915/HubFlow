from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from hubflow.billing.models import Payment
from hubflow.boards.activity import record
from hubflow.boards.models import Card, CardMove
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.reports.services import build_report, period_bounds
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db
TZ = ZoneInfo('America/Sao_Paulo')


@pytest.mark.parametrize(
    ('kind', 'ref', 'expected'),
    [
        ('week', date(2026, 10, 14), (date(2026, 10, 12), date(2026, 10, 18))),
        ('fortnight', date(2026, 10, 14), (date(2026, 10, 1), date(2026, 10, 15))),
        ('fortnight', date(2026, 10, 20), (date(2026, 10, 16), date(2026, 10, 31))),
        ('month', date(2026, 2, 10), (date(2026, 2, 1), date(2026, 2, 28))),
    ],
)
def test_limites_do_periodo(kind, ref, expected):
    assert period_bounds(kind, ref) == expected


def at(day, hour=10):
    return datetime(2026, 10, day, hour, tzinfo=TZ)


@pytest.fixture
def data(loja, user):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='x', name='Bob')
    beta = Project.objects.create(client=Client.objects.create(name='Beta'), name='Site', owner='b', repo='s')
    login = Card.objects.create(project=loja, title='Login')
    cart = Card.objects.create(project=loja, title='Carrinho')
    other = Card.objects.create(project=beta, title='De outro cliente')
    Card.objects.filter(id__in=[login.id, cart.id, other.id]).update(created=at(5))
    TimeEntry.objects.create(card=login, user=user, started_at=at(6), ended_at=at(6, 12))  # 2h
    TimeEntry.objects.create(card=cart, user=bob, started_at=at(7), ended_at=at(7, 11))  # 1h
    TimeEntry.objects.create(card=login, user=user, started_at=at(20), ended_at=at(20, 15))  # fora do período
    TimeEntry.objects.create(card=other, user=bob, started_at=at(6), ended_at=at(6, 18))  # outro cliente
    move = CardMove.objects.create(card=login, from_column='qa', to_column='done')
    CardMove.objects.filter(id=move.id).update(created=at(9))
    event = record(cart, 'sla_breached', None, column='qa', hours=24)
    type(event).objects.filter(id=event.id).update(created=at(8))
    Payment.objects.create(
        project=loja, hourly_rate=100, fixed_value=500, issue_date=date(2026, 10, 10), status='paid'
    )
    Payment.objects.create(project=loja, hourly_rate=100, fixed_value=300, issue_date=date(2026, 10, 11))
    Payment.objects.create(project=beta, hourly_rate=100, fixed_value=999, issue_date=date(2026, 10, 10))
    return {'login': login, 'cart': cart}


def test_relatorio_do_cliente_na_quinzena(loja, data, django_assert_max_num_queries):
    with django_assert_max_num_queries(8):
        report = build_report(date(2026, 10, 1), date(2026, 10, 15), client_id=loja.client_id)

    assert report['period'] == {'start': date(2026, 10, 1), 'end': date(2026, 10, 15)}
    assert report['hours']['total'] == 3.0
    assert report['hours']['by_user'] == [{'name': 'Ana', 'hours': 2.0}, {'name': 'Bob', 'hours': 1.0}]
    assert report['hours']['by_card'][0] == {
        'project': 'Loja',
        'number': data['login'].number,
        'title': 'Login',
        'hours': 2.0,
    }
    assert report['cards'] == {'created': 2, 'done': 1, 'avg_days_to_done': 4.0}
    assert report['sla_breached'] == 1
    assert report['billing'] == {'received': 500, 'pending': 300}


def test_relatorio_de_um_projeto_sem_faturamento(loja, data):
    report = build_report(date(2026, 10, 1), date(2026, 10, 15), project_id=loja.id, with_billing=False)

    assert report['hours']['total'] == 3.0 and report['billing'] is None
