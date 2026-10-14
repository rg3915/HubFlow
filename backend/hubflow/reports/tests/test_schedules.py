from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.reports.models import ReportSchedule
from hubflow.reports.services import send_due_reports

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def schedule(api, loja, **data):
    body = {'client': loja.client_id, 'frequency': 'week', 'emails': ['diretoria@hubflow.com']} | data
    return api.post('/api/report-schedules', body, **JSON)


def test_cria_e_o_primeiro_envio_e_no_fim_do_periodo_atual(api, loja, user):
    response = schedule(api, loja)

    assert response.status_code == 201
    data = response.json()
    assert data['scope'] == 'ACME' and data['frequency'] == 'week' and data['is_active'] is True
    created = ReportSchedule.objects.get()
    assert created.created_by == user and created.last_period_end is not None


def test_envia_cada_periodo_terminado_uma_vez(loja, user):
    ReportSchedule.objects.create(
        client=loja.client,
        frequency='week',
        emails=['diretoria@hubflow.com'],
        created_by=user,
        last_period_end=date(2026, 10, 4),
    )

    assert send_due_reports(today=date(2026, 10, 14)) == 1  # semana 5–11/10 terminou
    assert send_due_reports(today=date(2026, 10, 15)) == 0
    assert mail.outbox[0].to == ['diretoria@hubflow.com'] and '05/10/2026 a 11/10/2026' in mail.outbox[0].subject
    assert ReportSchedule.objects.get().last_period_end == date(2026, 10, 11)


def test_desligado_ou_sem_destinatario_nao_envia(loja, user):
    ReportSchedule.objects.create(client=loja.client, frequency='month', created_by=user, is_active=False)
    ReportSchedule.objects.create(client=loja.client, frequency='month', created_by=user)  # cliente sem e-mails

    assert send_due_reports(today=date(2026, 11, 2)) == 0


def test_validacoes(api, loja):
    assert schedule(api, loja, client=None).status_code == 400  # sem cliente nem projeto
    assert schedule(api, loja, frequency='dia').status_code == 400
    assert schedule(api, loja, emails=['x']).status_code == 400


def test_cada_pessoa_gerencia_os_seus(api, loja):
    rule_id = schedule(api, loja).json()['id']
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='x')
    bob_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=bob).key}'})

    assert bob_api.get('/api/report-schedules').json() == []
    assert bob_api.delete(f'/api/report-schedules/{rule_id}').status_code == 404
    edited = api.put(
        f'/api/report-schedules/{rule_id}',
        {'client': loja.client_id, 'frequency': 'month', 'is_active': False},
        **JSON,
    )
    assert edited.json()['frequency'] == 'month' and edited.json()['is_active'] is False
    assert api.delete(f'/api/report-schedules/{rule_id}').status_code == 204


def test_comando(loja, user, capsys):
    call_command('send_reports')

    assert 'Relatórios enviados: 0' in capsys.readouterr().out
