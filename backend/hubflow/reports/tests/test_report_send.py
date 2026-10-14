import pytest
from django.core import mail

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
BODY = {'period': 'month', 'date': '2026-10-14'}


def send(api, **data):
    return api.post('/api/reports/send', BODY | data, **JSON)


def test_envia_o_pdf_para_os_emails_informados(api, loja):
    response = send(api, client=loja.client_id, emails=['diretoria@hubflow.com', 'ti@hubflow.com'])

    assert response.status_code == 200
    assert response.json() == {'sent_to': ['diretoria@hubflow.com', 'ti@hubflow.com']}
    message = mail.outbox[0]
    assert message.to == ['diretoria@hubflow.com', 'ti@hubflow.com']
    assert 'ACME' in message.subject and '01/10/2026' in message.subject
    name, content, mimetype = message.attachments[0]
    assert name.endswith('.pdf') and content.startswith(b'%PDF') and mimetype == 'application/pdf'


def test_sem_emails_usa_os_do_projeto_ou_do_cliente(api, loja):
    loja.client.emails = ['acme@hubflow.com']
    loja.client.save()

    assert send(api, project=loja.id).json() == {'sent_to': ['acme@hubflow.com']}


def test_sem_destinatarios_ou_email_invalido_retorna_400(api, loja):
    assert send(api, project=loja.id).status_code == 400
    assert send(api, project=loja.id, emails=['nao-e-email']).status_code == 400
    assert mail.outbox == []
