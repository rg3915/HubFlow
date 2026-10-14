import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.billing.models import Payment
from hubflow.clients.models import Client
from hubflow.permissions.models import Membership
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


def api_for(role, email, client=None):
    person = User.objects.create_user(email=email, password='x', name=email.split('@')[0])
    person.groups.add(Group.objects.get(name=role))
    if client:
        Membership.objects.create(user=person, client=client)
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=person).key}'})


@pytest.fixture
def payments(loja):
    beta = Client.objects.create(name='Beta')
    site = Project.objects.create(client=beta, name='Site', owner='beta', repo='site')
    october = {'hourly_rate': 100, 'period_start': '2026-10-01', 'period_end': '2026-10-31'}
    return {
        'acme': Payment.objects.create(project=loja, fixed_value=1000, **october),
        'beta': Payment.objects.create(project=site, fixed_value=2000, **october),
    }


def test_leitura_nao_ve_pagamentos(payments):
    api = api_for('Leitura', 'leitura@hubflow.com')

    assert api.get('/api/payments').status_code == 403
    assert api.get('/api/payments/summary').status_code == 403
    assert api.get(f'/api/payments/{payments["acme"].id}').status_code == 403
    assert api.get('/api/dashboard/billing').json()['pending_total'] == '0.00'  # a home continua abrindo


def test_cliente_ve_so_os_pagamentos_dos_seus_clientes(loja, payments):
    api = api_for('Cliente', 'cli@hubflow.com', client=loja.client)

    assert [p['id'] for p in api.get('/api/payments').json()] == [payments['acme'].id]
    summary = api.get('/api/payments/summary').json()
    assert summary['received'] == '0.00' and summary['pending'] == '1000.00'
    assert [row['client_name'] for row in summary['by_client']] == ['ACME']
    assert api.get(f'/api/payments/{payments["acme"].id}').status_code == 200
    assert api.get(f'/api/payments/{payments["beta"].id}').status_code == 404
    assert api.post(f'/api/payments/{payments["acme"].id}/pay').status_code == 403


def test_gerente_ve_todos_mas_nao_gerencia(loja, payments):
    api = api_for('Gerente', 'ger@hubflow.com')
    payload = {'project_id': loja.id, 'hourly_rate': '100', 'month': '2026-11'}

    assert len(api.get('/api/payments').json()) == 2
    assert api.post('/api/payments', payload, **JSON).status_code == 403
    assert api.put(f'/api/payments/{payments["acme"].id}', payload, **JSON).status_code == 403
    assert api.post(f'/api/payments/{payments["acme"].id}/pay').status_code == 403
    assert api.post(f'/api/payments/{payments["acme"].id}/copy').status_code == 403
    assert api.delete(f'/api/payments/{payments["acme"].id}').status_code == 403


def test_financeiro_gerencia(loja, payments):
    api = api_for('Financeiro', 'fin@hubflow.com')
    payload = {'project_id': loja.id, 'hourly_rate': '100', 'month': '2026-11'}

    assert api.post('/api/payments', payload, **JSON).status_code == 201
    assert api.post(f'/api/payments/{payments["acme"].id}/pay').status_code == 200
    assert api.post(f'/api/payments/{payments["beta"].id}/copy').status_code == 201
    assert api.delete(f'/api/payments/{payments["beta"].id}').status_code == 204
