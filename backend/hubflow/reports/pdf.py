from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify


def scope_name(report):
    scope = report['scope']
    return scope['project'] or scope['client'] or 'Todos os projetos'


def file_name(report):
    period = report['period']
    return f'hubflow-{slugify(scope_name(report))}-{period["start"]:%Y-%m-%d}-a-{period["end"]:%Y-%m-%d}.pdf'


def render_report_html(report):
    title = f'Relatório {scope_name(report)}'
    context = {'report': report, 'scope_name': scope_name(report), 'title': title, 'generated': timezone.localtime()}
    return render_to_string('reports/report.html', context)


def render_report_pdf(report):
    from weasyprint import HTML  # importa só quando gera PDF (depende de bibliotecas do sistema)

    return HTML(string=render_report_html(report)).write_pdf()
