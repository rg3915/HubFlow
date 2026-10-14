from enum import Enum

import typer

from .client import fail, request
from .clients import parse_emails

app = typer.Typer(help='Projetos (um por repositório).', no_args_is_help=True)


class Provider(str, Enum):
    github = 'github'
    gitlab = 'gitlab'


def find_client(name):
    for client in request('GET', '/clients').json():
        if client['name'].lower() == name.lower():
            return client
    fail(f'Cliente "{name}" não encontrado. Veja os nomes com: hubflow client list')


def split_repo(value):
    owner, _, repo = value.partition('/')
    if not owner or not repo or '/' in repo:
        raise typer.BadParameter('Use o formato owner/repo, por exemplo: acme/loja')
    return owner, repo


@app.command()
def create(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    client: str = typer.Option(..., help='Nome do cliente dono do projeto.'),
    provider: Provider = typer.Option(..., help='github ou gitlab.'),
    repo: str = typer.Option(..., help='Repositório no formato owner/repo.', callback=lambda v: v),
    emails: str = typer.Option('', help='E-mails de notificação separados por vírgula.'),
):
    """Cria um projeto ligado a um repositório."""
    owner, repo_name = split_repo(repo)
    owner_client = find_client(client)
    body = {
        'client_id': owner_client['id'],
        'name': name,
        'provider': provider.value,
        'owner': owner,
        'repo': repo_name,
        'emails': parse_emails(emails),
    }
    project = request('POST', '/projects', json=body).json()
    typer.echo(f"Projeto #{project['id']} {project['name']} criado em {project['repository_url']}.")


@app.command('list')
def list_projects(client: str = typer.Option('', help='Filtra pelo nome do cliente.')):
    """Lista os projetos."""
    params = {'client': find_client(client)['id']} if client else {}
    projects = request('GET', '/projects', params=params).json()
    if not projects:
        typer.echo('Nenhum projeto cadastrado. Crie um com: hubflow project create NOME --client X --provider github --repo owner/repo')
        return
    for project in projects:
        status = '' if project['is_active'] else '  (inativo)'
        typer.echo(f"#{project['id']:<4} {project['client_name']} / {project['name']}  {project['repository_url']}{status}")
