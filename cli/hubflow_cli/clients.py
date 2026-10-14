import typer

from .client import request

app = typer.Typer(help='Clientes (donos dos projetos).', no_args_is_help=True)


def parse_emails(value):
    return [email.strip() for email in value.split(',') if email.strip()] if value else []


@app.command()
def create(
    name: str = typer.Argument(..., help='Nome do cliente.'),
    emails: str = typer.Option('', help='E-mails de notificação separados por vírgula.'),
):
    """Cria um cliente."""
    client = request('POST', '/clients', json={'name': name, 'emails': parse_emails(emails)}).json()
    typer.echo(f'Cliente #{client["id"]} {client["name"]} criado.')


@app.command('list')
def list_clients():
    """Lista os clientes."""
    clients = request('GET', '/clients').json()
    if not clients:
        typer.echo('Nenhum cliente cadastrado. Crie um com: hubflow client create NOME')
        return
    for client in clients:
        status = '' if client['is_active'] else '  (inativo)'
        emails = f'  {", ".join(client["emails"])}' if client['emails'] else ''
        typer.echo(f'#{client["id"]:<4} {client["name"]}{emails}{status}')
