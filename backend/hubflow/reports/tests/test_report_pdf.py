import pytest

from hubflow.boards.models import Card
from hubflow.reports.pdf import render_report_html

pytestmark = pytest.mark.django_db

PARAMS = {'period': 'month', 'date': '2026-10-14'}


def test_baixa_o_pdf(api, loja):
    response = api.get('/api/reports/pdf', PARAMS | {'client': loja.client_id})

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')
    assert response['Content-Disposition'] == 'attachment; filename="hubflow-acme-2026-10-01-a-2026-10-31.pdf"'


def test_html_do_relatorio_tem_os_numeros(api, user, loja):
    from datetime import date

    from hubflow.reports.api import report_for

    Card.objects.create(project=loja, title='Login')
    report = report_for(user, client=loja.client_id, period='month', ref=date.today())

    html = render_report_html(report)

    assert 'ACME' in html and 'Cards criados' in html and 'Faturamento' in html
    assert '<style>' in html  # CSS embutido: o PDF não depende de arquivos estáticos


def test_pdf_respeita_as_mesmas_validacoes(api):
    assert api.get('/api/reports/pdf', {'period': 'ano', 'date': '2026-10-01'}).status_code == 400


def test_navegador_le_o_nome_do_arquivo(api, loja, settings):
    response = api.get('/api/reports/pdf', PARAMS | {'client': loja.client_id}, headers={'Origin': settings.FRONTEND_URL})

    assert response['Access-Control-Expose-Headers'] == 'Content-Disposition'
