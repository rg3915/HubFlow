import datetime
import re
from pathlib import Path

import typer

from .client import format_hours, format_money, parse_iso_date, request
from .projects import find_client, find_project

app = typer.Typer(help='Relatórios por período (horas, cards, SLA e faturamento).', no_args_is_help=True)
schedules = typer.Typer(help='Relatórios enviados por e-mail ao fim de cada período.', no_args_is_help=True)
app.add_typer(schedules, name='schedule')

FREQUENCY = {'week': 'semanal', 'fortnight': 'quinzenal', 'month': 'mensal'}
ClientOpt = typer.Option('', '--client', help='Nome do cliente.')
ProjectOpt = typer.Option('', '--project', help='Nome do projeto.')
PeriodOpt = typer.Option('month', help='week, fortnight ou month.')
DateOpt = typer.Option('', '--date', help='Data dentro do período (AAAA-MM-DD; padrão: hoje).')
StartOpt = typer.Option('', '--start', help='Início (com --end, em vez de --period).')
EndOpt = typer.Option('', '--end', help='Fim.')


def scope(client, project):
    if not (client or project):
        raise typer.BadParameter('Informe --client ou --project.')
    if project:
        return {'project': find_project(project)['id']}
    return {'client': find_client(client)['id']}


def query(client, project, period, date, start, end):
    params = scope(client, project)
    if start or end:
        return params | {'start': parse_iso_date(start), 'end': parse_iso_date(end)}
    return params | {'period': period, 'date': parse_iso_date(date) or datetime.date.today().isoformat()}


def br(value):
    return datetime.date.fromisoformat(value).strftime('%d/%m/%Y')


@app.command()
def show(
    client: str = ClientOpt,
    project: str = ProjectOpt,
    period: str = PeriodOpt,
    date: str = DateOpt,
    start: str = StartOpt,
    end: str = EndOpt,
):
    """Mostra o relatório do período."""
    report = request('GET', '/reports', params=query(client, project, period, date, start, end)).json()
    window, name = report['period'], report['scope']['project'] or report['scope']['client']
    typer.echo(f'{name} · {window["label"]} de {br(window["start"])} a {br(window["end"])}')
    typer.echo(f'Horas: {format_hours(report["hours"]["total"])}')
    for row in report['hours']['by_user']:
        typer.echo(f'  {row["name"]}: {format_hours(row["hours"])}')
    cards = report['cards']
    lead = (
        f' · média de {cards["avg_days_to_done"]} dias até concluir' if cards['avg_days_to_done'] is not None else ''
    )
    typer.echo(f'Cards criados: {cards["created"]} · concluídos: {cards["done"]}{lead}')
    typer.echo(f'SLAs estourados: {report["sla_breached"]}')
    if report['billing']:
        billing = report['billing']
        typer.echo(f'Recebido: {format_money(billing["received"])} · pendente: {format_money(billing["pending"])}')


@app.command()
def pdf(
    client: str = ClientOpt,
    project: str = ProjectOpt,
    period: str = PeriodOpt,
    date: str = DateOpt,
    start: str = StartOpt,
    end: str = EndOpt,
    output: Path = typer.Option(Path('.'), help='Pasta (ou arquivo .pdf) onde salvar.'),
):
    """Baixa o relatório em PDF."""
    response = request('GET', '/reports/pdf', params=query(client, project, period, date, start, end))
    found = re.search(r'filename="([^"]+)"', response.headers.get('Content-Disposition', ''))
    target = output if output.suffix == '.pdf' else output / (found.group(1) if found else 'relatorio.pdf')
    target.write_bytes(response.content)
    typer.echo(f'PDF salvo em {target}')


@app.command()
def send(
    client: str = ClientOpt,
    project: str = ProjectOpt,
    period: str = PeriodOpt,
    date: str = DateOpt,
    start: str = StartOpt,
    end: str = EndOpt,
    email: list[str] = typer.Option([], help='Destinatário (repita; sem ele, os e-mails do projeto/cliente).'),
):
    """Envia o relatório em PDF por e-mail."""
    body = query(client, project, period, date, start, end) | {'emails': email}
    sent = request('POST', '/reports/send', json=body).json()['sent_to']
    typer.echo(f'Relatório enviado para {", ".join(sent)}.')


@schedules.command('list')
def list_schedules():
    """Lista os seus relatórios agendados."""
    items = request('GET', '/report-schedules').json()
    if not items:
        typer.echo('Nenhum relatório agendado. Crie com: hubflow report schedule add --client NOME --frequency week')
    for item in items:
        to = ', '.join(item['emails']) or 'e-mails do cliente/projeto'
        state = 'ligado' if item['is_active'] else 'desligado'
        typer.echo(f'#{item["id"]}  {item["scope"]}  {FREQUENCY[item["frequency"]]}  {to}  {state}')


@schedules.command('add')
def add_schedule(
    client: str = ClientOpt,
    project: str = ProjectOpt,
    frequency: str = typer.Option('month', help='week, fortnight ou month.'),
    email: list[str] = typer.Option([], help='Destinatário (repita; sem ele, os e-mails do projeto/cliente).'),
):
    """Agenda o envio do relatório ao fim de cada período."""
    item = request(
        'POST', '/report-schedules', json=scope(client, project) | {'frequency': frequency, 'emails': email}
    ).json()
    typer.echo(f'Relatório {FREQUENCY[item["frequency"]]} de {item["scope"]} agendado (#{item["id"]}).')


@schedules.command('remove')
def remove_schedule(schedule_id: int = typer.Argument(..., help='Número do agendamento.')):
    """Cancela um relatório agendado."""
    request('DELETE', f'/report-schedules/{schedule_id}')
    typer.echo(f'Agendamento #{schedule_id} removido.')
