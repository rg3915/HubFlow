import httpx
import typer

from . import cards, clients, config, payments, projects, sprints
from .cards import board_cards, local_time
from .client import format_hours, request
from .projects import find_project

app = typer.Typer(help='HubFlow: clientes, projetos e cards por linha de comando.', no_args_is_help=True)


app.add_typer(clients.app, name='client')
app.add_typer(projects.app, name='project')
app.add_typer(cards.app, name='card')
app.add_typer(sprints.app, name='sprint')
app.add_typer(payments.app, name='payment')


@app.callback()
def main():
    pass


@app.command()
def login(
    email: str = typer.Option(..., prompt='E-mail'),
    password: str = typer.Option(..., prompt='Senha', hide_input=True),
):
    """Entra com e-mail e senha e guarda o token."""
    response = request('POST', '/auth/login', auth=False, json={'email': email, 'password': password})
    config.save_config({'url': config.api_url(), 'token': response.json()['token']})
    typer.echo(f'Logado como {email}.')


@app.command()
def whoami():
    """Mostra o usuário logado."""
    user = request('GET', '/auth/me').json()
    name = f' ({user["name"]})' if user['name'] else ''
    typer.echo(f'{user["email"]}{name}')


@app.command()
def logout():
    """Invalida o token e apaga a configuração local."""
    key = config.token()
    if key:
        httpx.post(f'{config.api_url()}/api/auth/logout', headers={'Authorization': f'Bearer {key}'})
    config.save_config({'url': config.api_url()})
    typer.echo('Sessão encerrada.')


@app.command()
def timesheets(
    project: str = typer.Option('', help='Só este projeto (padrão: todos).'),
    limit: int = typer.Option(10, help='Quantas entradas mostrar.'),
):
    """Últimas entradas de tempo, da mais recente à mais antiga.

    Ainda não há endpoint global de tempo: a CLI percorre os projetos, o quadro de cada um e o tempo de cada
    card (várias chamadas). Um endpoint dedicado virá junto com o dashboard.
    """
    projects = [find_project(project)] if project else request('GET', '/projects').json()
    rows = []
    for owner in projects:
        for card in board_cards(owner):
            for entry in request('GET', f'/cards/{card["id"]}/time').json()['entries']:
                rows.append((local_time(entry['started_at']), owner['name'], card, entry))
    if not rows:
        typer.echo('Nenhum tempo registrado.')
        return
    rows.sort(key=lambda row: row[0], reverse=True)
    for started, name, card, entry in rows[:limit]:
        spent = 'rodando' if entry['is_running'] else format_hours(entry['hours'])
        typer.echo(f'{started:%d/%m/%Y}  {name}  #{card["number"]} {card["title"]}  {spent}  {entry["user"]["email"]}')
