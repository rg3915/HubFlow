import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS
from tests.test_project import CLIENTS

REPORT = {
    'period': {'kind': 'month', 'label': 'Mês', 'start': '2026-10-01', 'end': '2026-10-31'},
    'scope': {'client': 'ACME', 'project': None},
    'hours': {'total': 3.0, 'by_user': [{'name': 'Ana', 'hours': 2.0}, {'name': 'Bob', 'hours': 1.0}], 'by_card': []},
    'cards': {'created': 4, 'done': 2, 'avg_days_to_done': 3.5},
    'sla_breached': 1,
    'billing': {'received': '500.00', 'pending': '300.00'},
}


@pytest.fixture(autouse=True)
def api():
    save_config({'url': 'http://api.test', 'token': 'abc123'})
    with respx.mock:
        respx.get('http://api.test/api/clients').mock(return_value=Response(200, json=CLIENTS))
        respx.get('http://api.test/api/projects').mock(return_value=Response(200, json=PROJECTS))
        yield


def test_show_do_mes_do_cliente(run):
    route = respx.get('http://api.test/api/reports').mock(return_value=Response(200, json=REPORT))

    result = run('report', 'show', '--client', 'ACME', '--date', '2026-10-14')

    assert result.exit_code == 0, result.output
    assert dict(route.calls.last.request.url.params) == {'client': '1', 'period': 'month', 'date': '2026-10-14'}
    for text in [
        'ACME · Mês de 01/10/2026 a 31/10/2026',
        'Horas: 3h',
        'Ana: 2h',
        'Cards criados: 4',
        'concluídos: 2',
        'SLAs estourados: 1',
        'Recebido: R$ 500,00',
    ]:
        assert text in result.output


def test_show_com_datas_livres(run):
    route = respx.get('http://api.test/api/reports').mock(return_value=Response(200, json=REPORT))

    run('report', 'show', '--project', 'Loja', '--start', '2026-10-01', '--end', '2026-10-05')

    assert dict(route.calls.last.request.url.params) == {'project': '5', 'start': '2026-10-01', 'end': '2026-10-05'}


def test_pdf_salva_o_arquivo(run, tmp_path):
    headers = {'Content-Disposition': 'attachment; filename="hubflow-acme-2026-10-01-a-2026-10-31.pdf"'}
    respx.get('http://api.test/api/reports/pdf').mock(
        return_value=Response(200, content=b'%PDF-1.7 ...', headers=headers)
    )

    result = run('report', 'pdf', '--client', 'ACME', '--date', '2026-10-14', '--output', str(tmp_path))

    assert result.exit_code == 0, result.output
    saved = tmp_path / 'hubflow-acme-2026-10-01-a-2026-10-31.pdf'
    assert saved.read_bytes().startswith(b'%PDF') and str(saved) in result.output


def test_send(run):
    route = respx.post('http://api.test/api/reports/send').mock(
        return_value=Response(200, json={'sent_to': ['a@hubflow.com']})
    )

    result = run(
        'report', 'send', '--client', 'ACME', '--period', 'week', '--date', '2026-10-14', '--email', 'a@hubflow.com'
    )

    assert json.loads(route.calls.last.request.read()) == {
        'client': 1,
        'period': 'week',
        'date': '2026-10-14',
        'emails': ['a@hubflow.com'],
    }
    assert 'Relatório enviado para a@hubflow.com.' in result.output


def test_schedule_add_list_remove(run):
    item = {
        'id': 3,
        'client_id': 1,
        'project_id': None,
        'scope': 'ACME',
        'frequency': 'week',
        'emails': [],
        'is_active': True,
        'last_period_end': '2026-10-11',
    }
    add = respx.post('http://api.test/api/report-schedules').mock(return_value=Response(201, json=item))
    respx.get('http://api.test/api/report-schedules').mock(return_value=Response(200, json=[item]))
    delete = respx.delete('http://api.test/api/report-schedules/3').mock(return_value=Response(204))

    run('report', 'schedule', 'add', '--client', 'ACME', '--frequency', 'week')
    assert json.loads(add.calls.last.request.read()) == {'client': 1, 'frequency': 'week', 'emails': []}
    assert '#3  ACME  semanal  e-mails do cliente/projeto  ligado' in run('report', 'schedule', 'list').output
    assert run('report', 'schedule', 'remove', '3').exit_code == 0 and delete.called


def test_sem_cliente_nem_projeto(run):
    result = run('report', 'show')

    assert result.exit_code == 2 and '--client' in result.output
