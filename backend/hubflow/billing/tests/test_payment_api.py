from datetime import date

import pytest

from hubflow.billing.models import Payment
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def sprint(loja):
    return Sprint.objects.create(project=loja)


def payload(sprint, **overrides):
    return {
        'sprint_id': sprint.id,
        'hourly_rate': '150.00',
        'estimated_hours': '40',
        'description': 'Outubro',
    } | overrides


def test_cria_pagamento(api, sprint):
    response = api.post('/api/payments', payload(sprint), **JSON)

    assert response.status_code == 201
    data = response.json()
    assert data['status'] == 'pending'
    assert data['estimated_value'] == '6000.00'
    assert data['client_name'] == 'ACME' and data['project_name'] == 'Loja' and data['sprint_number'] == 1
    assert data['spent_hours'] == '0.00' and data['total_value'] == '0.00'


def test_valor_hora_zero_retorna_422(api, sprint):
    assert api.post('/api/payments', payload(sprint, hourly_rate='0'), **JSON).status_code == 422


def test_sprint_inexistente_retorna_404(api, sprint):
    assert api.post('/api/payments', payload(sprint, sprint_id=999), **JSON).status_code == 404


def test_lista_com_filtros(api, loja, sprint):
    other_project = loja.__class__.objects.create(
        client=loja.client.__class__.objects.create(name='Beta'), name='Site', provider='github', owner='b', repo='s'
    )
    other_sprint = Sprint.objects.create(project=other_project)
    Payment.objects.create(sprint=sprint, hourly_rate=100, issue_date=date(2026, 10, 1))
    paid = Payment.objects.create(sprint=other_sprint, hourly_rate=100, issue_date=date(2025, 3, 1))
    paid.pay()

    assert len(api.get('/api/payments').json()) == 2
    assert [p['client_name'] for p in api.get(f'/api/payments?client={loja.client_id}').json()] == ['ACME']
    assert [p['client_name'] for p in api.get('/api/payments?status=paid').json()] == ['Beta']
    assert [p['client_name'] for p in api.get('/api/payments?year=2026').json()] == ['ACME']


def test_edita_pagamento(api, sprint):
    payment = Payment.objects.create(sprint=sprint, hourly_rate=100)

    response = api.put(
        f'/api/payments/{payment.id}',
        payload(sprint, invoice_number='NF-7', issue_date='2026-10-14', fixed_value='1234.50'),
        **JSON,
    )

    assert response.status_code == 200
    payment.refresh_from_db()
    assert (payment.invoice_number, str(payment.issue_date), str(payment.fixed_value)) == (
        'NF-7',
        '2026-10-14',
        '1234.50',
    )
    assert response.json()['total_value'] == '1234.50'


def test_paga_e_copia(api, sprint):
    payment = Payment.objects.create(sprint=sprint, hourly_rate=100, invoice_number='NF-1')

    paid = api.post(f'/api/payments/{payment.id}/pay').json()
    copy = api.post(f'/api/payments/{payment.id}/copy').json()

    assert (paid['status'], paid['payment_date']) == ('paid', date.today().isoformat())
    assert (copy['status'], copy['invoice_number'], copy['id'] != payment.id) == ('pending', '', True)


def test_exclui_pagamento(api, sprint):
    payment = Payment.objects.create(sprint=sprint, hourly_rate=100)

    assert api.delete(f'/api/payments/{payment.id}').status_code == 204
    assert not Payment.objects.filter(id=payment.id).exists()


def test_sprint_com_pagamento_nao_pode_ser_excluida(api, sprint):
    Payment.objects.create(sprint=sprint, hourly_rate=100)

    assert api.delete(f'/api/sprints/{sprint.id}').status_code == 400
