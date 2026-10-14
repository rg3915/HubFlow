from django.conf import settings
from django.core.mail import EmailMessage

from .pdf import file_name, render_report_pdf, scope_name


def send_report_email(report, recipients):
    """Manda o relatório em PDF anexado (envio manual e agendado usam esta função)."""
    period = report['period']
    when = f'{period["start"]:%d/%m/%Y} a {period["end"]:%d/%m/%Y}'
    body = (
        f'Olá,\n\nSegue o relatório de {scope_name(report)} ({period["label"].lower()} de {when}) do HubFlow, '
        f'em PDF anexado: horas, cards criados e concluídos, SLA e faturamento do período.\n'
    )
    message = EmailMessage(
        subject=f'[HubFlow] Relatório {scope_name(report)} · {when}',
        body=body,
        to=recipients,
        from_email=settings.DEFAULT_FROM_EMAIL,
    )
    message.attach(file_name(report), render_report_pdf(report), 'application/pdf')
    message.send()
