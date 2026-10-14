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


@pytest.fixture
def sprint(loja):
    return Sprint.objects.create(project=loja)


def spend(card, user, hours):
    start = timezone.now() - timedelta(hours=hours + 1)
    TimeEntry.objects.create(card=card, user=user, started_at=start, ended_at=start + timedelta(hours=hours))


def test_pagamento_nasce_pendente_e_ligado_a_sprint(sprint):
    # RN-80, RN-81
    payment = Payment.objects.create(sprint=sprint, hourly_rate=Decimal('150'))

    assert payment.status == 'pending'
    assert payment.sprint == sprint
    assert payment.client == sprint.project.client
    assert payment.project == sprint.project
    assert (payment.invoice_number, payment.issue_date, payment.payment_date) == ('', None, None)


def test_valor_estimado_vem_das_horas_estimadas(sprint):
    payment = Payment.objects.create(sprint=sprint, hourly_rate=Decimal('150'), estimated_hours=Decimal('40'))

    assert payment.estimated_value == Decimal('6000.00')


def test_tempo_gasto_soma_as_entradas_dos_cards_da_sprint(loja, sprint, user):
    # RN-80
    a = Card.objects.create(project=loja, title='A', sprint=sprint)
    b = Card.objects.create(project=loja, title='B', sprint=sprint)
    other = Card.objects.create(project=loja, title='Outra sprint', sprint=Sprint.objects.create(project=loja))
    spend(a, user, 2)
    spend(b, user, 1.5)
    spend(other, user, 10)
    payment = Payment.objects.create(sprint=sprint, hourly_rate=Decimal('100'))

    assert payment.spent_hours == Decimal('3.50')
    assert payment.total_value == Decimal('350.00')


def test_valor_total_manual_prevalece(loja, sprint, user):
    a = Card.objects.create(project=loja, title='A', sprint=sprint)
    spend(a, user, 2)
    payment = Payment.objects.create(sprint=sprint, hourly_rate=Decimal('100'), fixed_value=Decimal('999'))

    assert payment.total_value == Decimal('999')


def test_pagar_marca_pago_com_a_data_de_hoje(sprint):
    # RN-81
    payment = Payment.objects.create(sprint=sprint, hourly_rate=Decimal('150'))

    payment.pay()

    payment.refresh_from_db()
    assert (payment.status, payment.payment_date) == ('paid', date.today())


def test_copiar_duplica_como_pendente(sprint):
    payment = Payment.objects.create(
        sprint=sprint,
        hourly_rate=Decimal('150'),
        estimated_hours=Decimal('10'),
        invoice_number='NF-1',
        description='Out',
    )
    payment.pay()

    copy = payment.copy()

    assert copy.id != payment.id
    assert (copy.status, copy.payment_date, copy.invoice_number) == ('pending', None, '')
    assert (copy.sprint, copy.hourly_rate, copy.estimated_hours, copy.description) == (
        sprint,
        Decimal('150'),
        Decimal('10'),
        'Out',
    )


def test_valor_hora_obrigatorio_e_positivo(sprint):
    with pytest.raises(ValidationError):
        Payment(sprint=sprint, hourly_rate=Decimal('0')).full_clean()
