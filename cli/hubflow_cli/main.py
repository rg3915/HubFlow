import httpx
import typer

from . import config
from .client import request

app = typer.Typer(help='HubFlow: clientes, projetos e cards por linha de comando.', no_args_is_help=True)


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
