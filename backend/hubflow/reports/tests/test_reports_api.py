from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.billing.models import Payment
from hubflow.clients.models import Client
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db


def api_for(role, loja=None):
    person = get_user_model().objects.create_user(email=f'{role.lower()}@hubflow.com', password='x')
    person.groups.add(Group.objects.get(name=role))
    if loja:
        Membership.objects.create(user=person, client=loja.client)
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=person).key}'})


def test_relatorio_do_mes_do_cliente(api, loja):
    Payment.objects.create(project=loja, hourly_rate=100, fixed_value=500, issue_date=date(2026, 10, 3), status='paid')

    data = api.get('/api/reports', {'client': loja.client_id, 'period': 'month', 'date': '2026-10-14'}).json()

    assert data['period'] == {'kind': 'month', 'label': 'Mês', 'start': '2026-10-01', 'end': '2026-10-31'}
    assert data['scope'] == {'client': 'ACME', 'project': None}
    assert data['billing'] == {'received': '500.00', 'pending': '0.00'}
    assert set(data) >= {'hours', 'cards', 'sla_breached'}


def test_datas_livres(api, loja):
    data = api.get('/api/reports', {'project': loja.id, 'start': '2026-10-01', 'end': '2026-10-05'}).json()

    assert data['period']['kind'] == 'custom' and data['scope']['project'] == 'Loja'


def test_parametros_invalidos(api, loja):
    assert api.get('/api/reports', {'period': 'ano', 'date': '2026-10-01'}).status_code == 400
    assert api.get('/api/reports', {'start': '2026-10-05', 'end': '2026-10-01'}).status_code == 400
    assert api.get('/api/reports', {}).status_code == 400


def test_cliente_de_fora_da_404(loja):
    other = Client.objects.create(name='Beta')
    reader = api_for('Leitura', loja)

    assert reader.get('/api/reports', {'client': other.id, 'period': 'month', 'date': '2026-10-01'}).status_code == 404


def test_faturamento_so_com_permissao_de_pagamentos(loja):
    Payment.objects.create(project=loja, hourly_rate=100, fixed_value=500, issue_date=date(2026, 10, 3))
    params = {'client': loja.client_id, 'period': 'month', 'date': '2026-10-14'}

    assert api_for('Leitura', loja).get('/api/reports', params).json()['billing'] is None
    assert api_for('Cliente', loja).get('/api/reports', params).json()['billing'] == {
        'received': '0.00',
        'pending': '500.00',
    }
