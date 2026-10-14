import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS
from tests.test_sprint import SPRINT

CLIENTS = [{'id': 1, 'name': 'ACME', 'emails': [], 'is_active': True}]
PAYMENT = {
    'id': 4,
    'sprint_id': 3,
    'sprint_number': 2,
    'period_start': None,
    'period_end': None,
    'scope': 'Sprint 2',
    'project_id': 5,
    'project_name': 'Loja',
    'client_id': 1,
    'client_name': 'ACME',
    'description': 'Outubro',
    'hourly_rate': '150.00',
    'estimated_hours': '40.00',
    'estimated_value': '6000.00',
    'spent_hours': '12.50',
    'fixed_value': None,
    'total_value': '1875.00',
    'invoice_number': '',
    'issue_date': '2026-10-14',
    'payment_date': None,
    'status': 'pending',
    'created': '2026-10-14T00:00:00Z',
}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
    respx.get('http://api.test/api/clients').mock(return_value=Response(200, json=CLIENTS))
    respx.get('http://api.test/api/projects/5/sprints').mock(return_value=Response(200, json=[SPRINT]))


def body(route):
    return json.loads(route.calls.last.request.read())


@respx.mock
def test_payment_create_resolve_projeto_e_sprint(run):
    route = respx.post('http://api.test/api/payments').mock(return_value=Response(201, json=PAYMENT))

    result = run(
        'payment',
        'create',
        '--project',
        'Loja',
        '--sprint',
        '2',
        '--rate',
        '150',
        '--hours',
        '40',
        '--description',
        'Outubro',
        '--issue-date',
        '2026-10-14',
    )

    assert result.exit_code == 0, result.output
    sent = body(route)
    assert sent['project_id'] == 5 and sent['sprint_id'] == 3 and sent['month'] is None
    assert sent['hourly_rate'] == '150' and sent['estimated_hours'] == '40'
    assert sent['issue_date'] == '2026-10-14' and sent['description'] == 'Outubro'
    assert '#4' in result.output and 'R$' in result.output


@respx.mock
def test_payment_create_sprint_inexistente_falha(run):
    result = run('payment', 'create', '--project', 'Loja', '--sprint', '9', '--rate', '150')

    assert result.exit_code == 1
    assert 'Sprint 9' in result.output


@respx.mock
def test_payment_list(run):
    paid = PAYMENT | {'id': 5, 'status': 'paid', 'invoice_number': 'NF-7', 'payment_date': '2026-10-20'}
    respx.get('http://api.test/api/payments').mock(return_value=Response(200, json=[PAYMENT, paid]))

    result = run('payment', 'list')

    assert result.exit_code == 0, result.output
    assert '#4' in result.output and 'pendente' in result.output and 'ACME' in result.output
    assert '#5' in result.output and 'pago' in result.output and 'NF-7' in result.output


@respx.mock
def test_payment_list_filtra_por_cliente_e_status(run):
    route = respx.get('http://api.test/api/payments', params={'client': '1', 'status': 'paid'}).mock(
        return_value=Response(200, json=[])
    )

    result = run('payment', 'list', '--client', 'ACME', '--status', 'paid')

    assert route.called
    assert 'Nenhum pagamento' in result.output


@respx.mock
def test_payment_pay(run):
    route = respx.post('http://api.test/api/payments/4/pay').mock(
        return_value=Response(200, json=PAYMENT | {'status': 'paid', 'payment_date': '2026-10-14'})
    )

    result = run('payment', 'pay', '4')

    assert result.exit_code == 0, result.output
    assert route.called and 'pago' in result.output


@respx.mock
def test_payment_copy(run):
    route = respx.post('http://api.test/api/payments/4/copy').mock(
        return_value=Response(201, json=PAYMENT | {'id': 9})
    )

    result = run('payment', 'copy', '4')

    assert result.exit_code == 0, result.output
    assert route.called and '#9' in result.output


@respx.mock
def test_payment_summary(run):
    summary = {
        'received': '3000.00',
        'pending': '800.00',
        'by_client': [{'client_id': 1, 'client_name': 'ACME', 'received': '3000.00', 'pending': '800.00'}],
        'by_month': [{'month': '2026-10', 'received': '3000.00', 'pending': '800.00'}],
        'years': [2026],
    }
    respx.get('http://api.test/api/payments/summary').mock(return_value=Response(200, json=summary))

    result = run('payment', 'summary')

    assert result.exit_code == 0, result.output
    assert (
        '3.000,00' in result.output
        and '800,00' in result.output
        and 'ACME' in result.output
        and '2026-10' in result.output
    )


@respx.mock
def test_payment_create_mensal(run):
    monthly = PAYMENT | {'sprint_id': None, 'sprint_number': None, 'scope': '01/10/2026 a 31/10/2026'}
    route = respx.post('http://api.test/api/payments').mock(return_value=Response(201, json=monthly))

    result = run('payment', 'create', '--project', 'Loja', '--month', '2026-10', '--rate', '150')

    assert result.exit_code == 0, result.output
    sent = body(route)
    assert sent['sprint_id'] is None and sent['month'] == '2026-10' and sent['project_id'] == 5
    assert '01/10/2026' in result.output


@respx.mock
def test_payment_create_exige_sprint_ou_mes(run):
    assert run('payment', 'create', '--project', 'Loja', '--rate', '150').exit_code != 0
    both = run('payment', 'create', '--project', 'Loja', '--rate', '150', '--sprint', '2', '--month', '2026-10')
    assert both.exit_code != 0
