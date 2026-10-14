import typer

from .client import fail, format_money, parse_iso_date, request
from .projects import find_client, find_project
from .sprints import find_sprint

app = typer.Typer(help='Pagamentos por sprint.', no_args_is_help=True)

STATUS = {'pending': 'pendente', 'paid': 'pago'}


def describe(payment):
    invoice = f'  NF {payment["invoice_number"]}' if payment['invoice_number'] else ''
    when = payment['issue_date'] or '—'
    where = f'{payment["client_name"]} / {payment["project_name"]}  {payment["scope"]}'
    money = format_money(payment['total_value'])
    return f'#{payment["id"]:<4} {where}  {money}  {when}{invoice}  ({STATUS[payment["status"]]})'


@app.command()
def create(
    project: str = typer.Option(..., help='Nome do projeto.'),
    sprint: int | None = typer.Option(None, help='Número da sprint (opcional).'),
    month: str = typer.Option('', help='Mês do período, AAAA-MM (opcional; use sprint ou mês).'),
    rate: str = typer.Option(..., help='Valor por hora, ex.: 150.'),
    hours: str = typer.Option('', help='Horas estimadas (opcional).'),
    fixed: str = typer.Option('', help='Valor fechado (opcional; vale no lugar de horas × valor/hora).'),
    description: str = typer.Option('', help='Descrição.'),
    invoice: str = typer.Option('', help='Número da NF.'),
    issue_date: str = typer.Option('', '--issue-date', help='Emissão AAAA-MM-DD.'),
):
    """Cria um pagamento do projeto, por sprint ou por mês."""
    if (sprint is None) == (not month):
        raise typer.BadParameter('Informe --sprint N ou --month AAAA-MM (um dos dois).')
    owner = find_project(project)
    body = {
        'project_id': owner['id'],
        'sprint_id': find_sprint(project, sprint)['id'] if sprint is not None else None,
        'month': month or None,
        'hourly_rate': rate,
        'estimated_hours': hours or None,
        'fixed_value': fixed or None,
        'description': description,
        'invoice_number': invoice,
        'issue_date': parse_iso_date(issue_date),
    }
    payment = request('POST', '/payments', json=body).json()
    typer.echo(f'Pagamento criado: {describe(payment)}')


@app.command('list')
def list_payments(
    client: str = typer.Option('', help='Filtra pelo nome do cliente.'),
    status: str = typer.Option('', help='pending ou paid.'),
    year: int | None = typer.Option(None, help='Ano de emissão.'),
):
    """Lista os pagamentos."""
    params = {}
    if client:
        params['client'] = find_client(client)['id']
    if status:
        if status not in STATUS:
            fail('Status inválido. Use: pending ou paid')
        params['status'] = status
    if year:
        params['year'] = year
    payments = request('GET', '/payments', params=params).json()
    if not payments:
        typer.echo('Nenhum pagamento encontrado.')
        return
    for payment in payments:
        typer.echo(describe(payment))


@app.command()
def pay(payment_id: int = typer.Argument(..., help='Id do pagamento.')):
    """Marca o pagamento como pago com a data de hoje."""
    payment = request('POST', f'/payments/{payment_id}/pay').json()
    typer.echo(f'Pagamento #{payment["id"]} marcado como pago em {payment["payment_date"]}.')


@app.command()
def copy(payment_id: int = typer.Argument(..., help='Id do pagamento.')):
    """Duplica o pagamento como pendente."""
    payment = request('POST', f'/payments/{payment_id}/copy').json()
    typer.echo(f'Cópia criada: {describe(payment)}')


@app.command()
def summary(
    client: str = typer.Option('', help='Filtra pelo nome do cliente.'),
    year: int | None = typer.Option(None, help='Ano de emissão.'),
):
    """Recebido, pendente, por cliente e por mês."""
    params = {}
    if client:
        params['client'] = find_client(client)['id']
    if year:
        params['year'] = year
    data = request('GET', '/payments/summary', params=params).json()
    typer.echo(f'Recebido: {format_money(data["received"])}   Pendente: {format_money(data["pending"])}')
    for title, rows, key in (
        ('Por cliente:', data['by_client'], 'client_name'),
        ('Por mês:', data['by_month'], 'month'),
    ):
        if not rows:
            continue
        typer.echo(title)
        for row in rows:
            totals = f'{format_money(row["received"]):>16} recebido  {format_money(row["pending"]):>16} pendente'
            typer.echo(f'  {row[key]:<20} {totals}')
