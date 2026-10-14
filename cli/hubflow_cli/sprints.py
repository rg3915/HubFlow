import typer

from .client import fail, parse_iso_date, request
from .projects import find_project

app = typer.Typer(help='Sprints do projeto.', no_args_is_help=True)


def describe(sprint):
    name = f' · {sprint["name"]}' if sprint['name'] else ''
    status = 'aberta' if sprint['is_open'] else 'fechada'
    return f'Sprint {sprint["number"]}{name}  {sprint["cards_count"]} cards  ({status})'


def find_sprint(project_name, number):
    project = find_project(project_name)
    for sprint in request('GET', f'/projects/{project["id"]}/sprints').json():
        if sprint['number'] == number:
            return sprint
    fail(f'Sprint {number} não existe em {project["name"]}. Veja com: hubflow sprint list --project {project["name"]}')


@app.command()
def create(
    project: str = typer.Option(..., help='Nome do projeto.'),
    name: str = typer.Option('', help='Nome da sprint (opcional).'),
    milestone: int | None = typer.Option(None, help='Id do milestone (opcional).'),
    start: str = typer.Option('', help='Início AAAA-MM-DD (opcional).'),
    end: str = typer.Option('', help='Fim AAAA-MM-DD (opcional).'),
):
    """Cria a próxima sprint do projeto."""
    owner = find_project(project)
    body = {'name': name, 'milestone_id': milestone}
    body |= {'start_date': parse_iso_date(start), 'end_date': parse_iso_date(end)}
    sprint = request('POST', f'/projects/{owner["id"]}/sprints', json=body).json()
    typer.echo(f'{describe(sprint)} criada em {owner["name"]}.')


@app.command('list')
def list_sprints(project: str = typer.Option(..., help='Nome do projeto.')):
    """Lista as sprints do projeto, da mais recente para a mais antiga."""
    owner = find_project(project)
    sprints = request('GET', f'/projects/{owner["id"]}/sprints').json()
    if not sprints:
        typer.echo('Nenhuma sprint ainda. A primeira é criada ao criar um card, ou com: hubflow sprint create')
        return
    for sprint in sprints:
        typer.echo(describe(sprint))


@app.command()
def close(
    number: int = typer.Argument(..., help='Número da sprint.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Fecha a sprint (os cards continuam onde estão)."""
    sprint = find_sprint(project, number)
    closed = request('POST', f'/sprints/{sprint["id"]}/close').json()
    typer.echo(f'Sprint {closed["number"]} fechada.')
