from enum import Enum

import typer

from .client import find_by_name, request
from .clients import parse_emails

app = typer.Typer(help='Projetos (um por repositório).', no_args_is_help=True)


class Provider(str, Enum):
    github = 'github'
    gitlab = 'gitlab'


def find_client(name):
    return find_by_name('/clients', name, 'Cliente', 'hubflow client list')


def find_project(name):
    return find_by_name('/projects', name, 'Projeto', 'hubflow project list')


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
    repo: str = typer.Option(..., help='Repositório no formato owner/repo.'),
    emails: str = typer.Option('', help='E-mails de notificação separados por vírgula.'),
    full: bool = typer.Option(False, '--full', help='Cria também o cliente (se não existir) e a sprint 1.'),
    milestone: str = typer.Option('', help='Com --full: título do milestone da sprint 1 (opcional).'),
):
    """Cria um projeto ligado a um repositório."""
    owner, repo_name = split_repo(repo)
    if full:
        body = {
            'client_name': client,
            'name': name,
            'provider': provider.value,
            'owner': owner,
            'repo': repo_name,
            'emails': parse_emails(emails),
            'milestone_title': milestone,
        }
        created = request('POST', '/projects/full', json=body).json()
        project, sprint = created['project'], created['sprint']
        extra = f' e milestone {created["milestone"]["title"]}' if created['milestone'] else ''
        where = f'{created["client"]["name"]} com a Sprint {sprint["number"]}{extra}'
        typer.echo(f'Projeto #{project["id"]} {project["name"]} criado em {where}.')
        return
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
    typer.echo(f'Projeto #{project["id"]} {project["name"]} criado em {project["repository_url"]}.')


@app.command('list')
def list_projects(client: str = typer.Option('', help='Filtra pelo nome do cliente.')):
    """Lista os projetos."""
    params = {'client': find_client(client)['id']} if client else {}
    projects = request('GET', '/projects', params=params).json()
    if not projects:
        typer.echo('Nenhum projeto cadastrado. Crie um com:')
        typer.echo('  hubflow project create NOME --client CLIENTE --provider github --repo owner/repo')
        return
    for project in projects:
        status = '' if project['is_active'] else '  (inativo)'
        title = f'{project["client_name"]} / {project["name"]}'
        typer.echo(f'#{project["id"]:<4} {title}  {project["repository_url"]}{status}')


EVENTS = {'created': 'card criado', 'moved': 'card movido', 'done': 'card concluído'}
PROJECT_FIELDS = (
    'client_id',
    'name',
    'provider',
    'owner',
    'repo',
    'description',
    'emails',
    'is_active',
    'notify_on_created',
    'notify_on_moved',
    'notify_on_done',
)


def update_project(project, **changes):
    """PUT com o projeto inteiro (a API não tem PATCH), aplicando só as mudanças pedidas."""
    body = {field: project[field] for field in PROJECT_FIELDS} | changes
    return request('PUT', f'/projects/{project["id"]}', json=body).json()


def parse_events(value):
    events = [e.strip() for e in value.split(',') if e.strip()]
    unknown = [e for e in events if e not in EVENTS]
    if unknown:
        raise typer.BadParameter(f'Evento desconhecido: {", ".join(unknown)}. Use: created, moved, done')
    return events


def show_notify(project):
    for key, label in EVENTS.items():
        state = 'ligado' if project[f'notify_on_{key}'] else 'desligado'
        typer.echo(f'  {label:<16} {state}')


@app.command()
def notify(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    on: str = typer.Option('', help='Eventos a ligar, separados por vírgula: created, moved, done.'),
    off: str = typer.Option('', help='Eventos a desligar, separados por vírgula.'),
):
    """Liga ou desliga os avisos por e-mail do projeto; sem opções, mostra o estado."""
    project = find_project(name)
    changes = {f'notify_on_{e}': True for e in parse_events(on)} | {f'notify_on_{e}': False for e in parse_events(off)}
    if changes:
        project = update_project(project, **changes)
    typer.echo(f'Avisos de {project["name"]}:')
    show_notify(project)


@app.command()
def emails(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    set_emails: str = typer.Option(..., '--set', help='E-mails separados por vírgula. Vazio = usa os do cliente.'),
):
    """Define os e-mails que recebem os avisos do projeto."""
    project = update_project(find_project(name), emails=parse_emails(set_emails))
    if project['emails']:
        typer.echo(f'Avisos de {project["name"]} vão para: {", ".join(project["emails"])}')
    else:
        typer.echo(f'{project["name"]} sem e-mails próprios: os avisos vão para os e-mails do cliente.')


def show_repo(settings):
    yes_no = lambda value: 'sim' if value else 'não'  # noqa: E731
    typer.echo(f'Repositório: {settings["repository_url"]} ({settings["provider"]})')
    typer.echo(f'  token: {yes_no(settings["has_token"])}')
    if settings['provider'] == 'gitlab':
        typer.echo(f'  id do projeto no GitLab: {settings["gitlab_project_id"] or "—"}')
    typer.echo(f'  criar issue ao criar card: {yes_no(settings["create_issues"])}')
    typer.echo(f'  segredo do webhook: {yes_no(settings["has_webhook_secret"])}')
    typer.echo(f'  URL do webhook: <sua-api>{settings["webhook_path"]}')


@app.command()
def repo(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    token: str | None = typer.Option(None, help='Token do GitHub/GitLab ("" apaga).'),
    gitlab_id: int | None = typer.Option(None, '--gitlab-id', help='Id numérico do projeto no GitLab.'),
    create_issues: bool | None = typer.Option(
        None, '--create-issues/--no-create-issues', help='Criar issue ao criar card.'
    ),
    webhook_secret: str | None = typer.Option(None, '--webhook-secret', help='Segredo do webhook ("" apaga).'),
):
    """Mostra ou altera a integração do projeto com o repositório."""
    project = find_project(name)
    current = request('GET', f'/projects/{project["id"]}/repo').json()
    changes = {'token': token, 'webhook_secret': webhook_secret}
    if any(value is not None for value in (token, gitlab_id, create_issues, webhook_secret)):
        body = changes | {
            'gitlab_project_id': current['gitlab_project_id'] if gitlab_id is None else gitlab_id,
            'create_issues': current['create_issues'] if create_issues is None else create_issues,
        }
        current = request('PUT', f'/projects/{project["id"]}/repo', json=body).json()
    show_repo(current)


@app.command('repo-check')
def repo_check(name: str = typer.Argument(..., help='Nome do projeto.')):
    """Testa a conexão com o repositório."""
    project = find_project(name)
    data = request('POST', f'/projects/{project["id"]}/repo/check').json()
    visibility = 'privado' if data['private'] else 'público'
    typer.echo(f'Conectado a {data["name"]} ({visibility}), {data["open_issues"]} issues abertas.')


@app.command('import-issues')
def import_issues(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    include_closed: bool = typer.Option(
        False, '--include-closed', help='Traz também as issues fechadas (vão para Concluído).'
    ),
):
    """Importa as issues do repositório como cards."""
    project = find_project(name)
    data = request('POST', f'/projects/{project["id"]}/import-issues', json={'include_closed': include_closed}).json()
    typer.echo(f'{data["created"]} cards criados, {data["skipped"]} issues puladas (já importadas ou pull requests).')
