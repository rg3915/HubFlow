from enum import Enum

import typer

from .client import request
from .projects import find_project

app = typer.Typer(help='Cards do quadro.', no_args_is_help=True)


class Column(str, Enum):
    backlog = 'backlog'
    sprint = 'sprint'
    doing = 'doing'
    qa = 'qa'
    done = 'done'
    archived = 'archived'


@app.command()
def create(
    title: str = typer.Argument(..., help='Título do card.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    description: str = typer.Option('', help='Descrição.'),
):
    """Cria um card no Backlog do projeto."""
    owner = find_project(project)
    body = {'title': title, 'description': description}
    card = request('POST', f'/projects/{owner["id"]}/cards', json=body).json()
    typer.echo(f'Card #{card["number"]} {card["title"]} criado no Backlog de {owner["name"]}.')


@app.command('list')
def list_cards(
    project: str = typer.Option(..., help='Nome do projeto.'),
    column: Column | None = typer.Option(None, help='Mostra só esta coluna.'),
):
    """Mostra o quadro do projeto, coluna a coluna."""
    owner = find_project(project)
    board = request('GET', f'/projects/{owner["id"]}/board', params={'archived': column == Column.archived}).json()
    columns = [c for c in board['columns'] if c['cards'] and (column is None or c['key'] == column.value)]
    if not columns:
        typer.echo('Nenhum card por aqui.')
        return
    for col in columns:
        typer.echo(f'{col["label"]} ({len(col["cards"])})')
        for card in col['cards']:
            typer.echo(f'  #{card["number"]:<4} {card["title"]}')
