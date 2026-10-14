from datetime import date, timedelta

import pytest

from hubflow.billing.models import Payment
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db


def first_of_month(day):
    return day.replace(day=1)


def test_faturamento_do_mes_e_do_anterior(api, loja):
    sprint = Sprint.objects.create(project=loja)
    today = date.today()
    this_month = first_of_month(today)
    last_month = first_of_month(this_month - timedelta(days=1))
    paid_now = Payment.objects.create(sprint=sprint, hourly_rate=100, fixed_value=1000, issue_date=this_month)
    Payment.objects.create(sprint=sprint, hourly_rate=100, fixed_value=500, issue_date=this_month)
    paid_before = Payment.objects.create(sprint=sprint, hourly_rate=100, fixed_value=2000, issue_date=last_month)
    Payment.objects.create(sprint=sprint, hourly_rate=100, fixed_value=300, issue_date=last_month)
    for payment in (paid_now, paid_before):
        payment.pay()

    data = api.get('/api/dashboard/billing').json()

    assert data['current'] == {'month': this_month.strftime('%Y-%m'), 'received': '1000.00', 'pending': '500.00'}
    assert data['previous'] == {'month': last_month.strftime('%Y-%m'), 'received': '2000.00', 'pending': '300.00'}
    assert data['pending_total'] == '800.00'


def test_sem_pagamentos(api):
    data = api.get('/api/dashboard/billing').json()

    assert data['current']['received'] == '0.00' and data['previous']['pending'] == '0.00'
    assert data['pending_total'] == '0.00'
