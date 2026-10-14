from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from hubflow.billing.models import Payment
from hubflow.boards.models import Card
from hubflow.sprints.models import Sprint
from hubflow.timetracking.models import TimeEntry

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def spend_on(card, user, day, hours):
    start = timezone.make_aware(timezone.datetime(day.year, day.month, day.day, 9, 0))
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=hours))


def test_pagamento_mensal_sem_sprint(loja, user):
    card = Card.objects.create(project=loja, title='A')
    spend_on(card, user, date(2026, 10, 5), 2)
    spend_on(card, user, date(2026, 10, 20), 1.5)
    spend_on(card, user, date(2026, 11, 1), 10)

    payment = Payment.objects.create(
        project=loja, hourly_rate=100, period_start=date(2026, 10, 1), period_end=date(2026, 10, 31)
    )

    assert payment.sprint is None
    assert payment.spent_hours == Decimal('3.50')
    assert payment.total_value == Decimal('350.00')


def test_pagamento_por_sprint_continua_valendo(loja, user):
    sprint = Sprint.objects.create(project=loja)
    card = Card.objects.create(project=loja, title='A', sprint=sprint)
    spend_on(card, user, date(2026, 9, 1), 4)

    payment = Payment.objects.create(project=loja, sprint=sprint, hourly_rate=100)

    assert payment.spent_hours == Decimal('4.00')


def test_exige_sprint_ou_periodo(loja):
    with pytest.raises(ValidationError):
        Payment(project=loja, hourly_rate=100).full_clean()


def test_sprint_tem_que_ser_do_projeto(loja):
    other = loja.__class__.objects.create(client=loja.client, name='App', provider='github', owner='a', repo='p')
    foreign = Sprint.objects.create(project=other)

    with pytest.raises(ValidationError):
        Payment(project=loja, sprint=foreign, hourly_rate=100).full_clean()


def test_periodo_invalido(loja):
    with pytest.raises(ValidationError):
        Payment(
            project=loja, hourly_rate=100, period_start=date(2026, 10, 31), period_end=date(2026, 10, 1)
        ).full_clean()


def test_copiar_mensal_avanca_um_mes(loja):
    payment = Payment.objects.create(
        project=loja, hourly_rate=100, period_start=date(2026, 10, 1), period_end=date(2026, 10, 31)
    )

    copy = payment.copy()

    assert (copy.period_start, copy.period_end) == (date(2026, 11, 1), date(2026, 11, 30))


def test_api_cria_mensal_com_month(api, loja):
    data = {'project_id': loja.id, 'hourly_rate': '120', 'month': '2026-10'}

    response = api.post('/api/payments', data, **JSON)

    assert response.status_code == 201
    body = response.json()
    assert (body['period_start'], body['period_end'], body['sprint_id']) == ('2026-10-01', '2026-10-31', None)
    assert body['project_name'] == 'Loja'


def test_api_sem_sprint_nem_periodo_retorna_400(api, loja):
    response = api.post('/api/payments', {'project_id': loja.id, 'hourly_rate': '120'}, **JSON)

    assert response.status_code == 400


def test_api_mes_invalido_retorna_422(api, loja):
    response = api.post('/api/payments', {'project_id': loja.id, 'hourly_rate': '120', 'month': '10/2026'}, **JSON)

    assert response.status_code == 422


def test_resumo_inclui_pagamentos_mensais(api, loja, user):
    card = Card.objects.create(project=loja, title='A')
    spend_on(card, user, date(2026, 10, 5), 2)
    Payment.objects.create(
        project=loja,
        hourly_rate=100,
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        issue_date=date(2026, 10, 31),
    )

    assert api.get('/api/payments/summary').json()['pending'] == '200.00'
