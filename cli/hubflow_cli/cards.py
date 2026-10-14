from enum import Enum

import typer

from .client import fail, request
from .projects import find_project

app = typer.Typer(help='Cards do quadro.', no_args_is_help=True)


class Column(str, Enum):
    backlog = 'backlog'
    sprint = 'sprint'
    doing = 'doing'
    qa = 'qa'
    done = 'done'
    archived = 'archived'


def find_card(project_name, number):
    """Localiza o card pelo número dentro do projeto, olhando o quadro inteiro (inclusive Arquivadas)."""
    project = find_project(project_name)
    board = request('GET', f'/projects/{project["id"]}/board', params={'archived': True}).json()
    for col in board['columns']:
        for card in col['cards']:
            if card['number'] == number:
                return card
    hint = f'hubflow card list --project {project["name"]}'
    fail(f'Card #{number} não existe em {project["name"]}. Veja os cards com: {hint}')


def column_label(key):
    return dict(COLUMN_LABELS)[key]


COLUMN_LABELS = (
    ('backlog', 'Backlog'),
    ('sprint', 'Sprint'),
    ('doing', 'Em desenvolvimento'),
    ('qa', 'QA'),
    ('done', 'Concluído'),
    ('archived', 'Arquivadas'),
)


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


@app.command()
def move(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    to: Column = typer.Option(..., help='Coluna de destino.'),
    position: int | None = typer.Option(None, help='Posição na coluna (0 = topo). Sem valor vai para o fim.'),
):
    """Move o card para outra coluna."""
    card = find_card(project, number)
    moved = request('POST', f'/cards/{card["id"]}/move', json={'column': to.value, 'position': position}).json()
    typer.echo(f'Card #{moved["number"]} {moved["title"]} movido para {column_label(moved["column"])}.')


@app.command()
def start(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Inicia o card: move para Em desenvolvimento."""
    card = find_card(project, number)
    started = request('POST', f'/cards/{card["id"]}/start').json()
    typer.echo(f'Card #{started["number"]} {started["title"]} em {column_label(started["column"])}.')
