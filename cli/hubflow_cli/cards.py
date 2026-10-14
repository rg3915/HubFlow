import datetime
from enum import Enum

import typer

from .client import fail, format_hours, parse_iso_date, request
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


def choose_sprint(owner, sprint_number, no_input):
    """RN-61 na CLI: --sprint N usa essa; sem sprint, pergunta se quer criar uma nova; sem nenhuma, a API cria."""
    sprints = request('GET', f'/projects/{owner["id"]}/sprints').json()
    if sprint_number is not None:
        chosen = next((s for s in sprints if s['number'] == sprint_number), None)
        if chosen is None:
            hint = f'hubflow sprint list --project {owner["name"]}'
            fail(f'Sprint {sprint_number} não existe em {owner["name"]}. Veja com: {hint}')
        return chosen['id']
    open_sprints = [s for s in sprints if s['is_open']]
    if not open_sprints:
        return None  # a API cria a próxima sprint sozinha
    latest = open_sprints[0]
    answer = (
        'n'
        if no_input
        else typer.prompt(
            f'Criar uma nova sprint? (não = usa a Sprint {latest["number"]}) [s/N]', default='n', show_default=False
        )
    )
    if answer.strip().lower() in ('s', 'sim', 'y', 'yes'):
        created = request('POST', f'/projects/{owner["id"]}/sprints', json={}).json()
        typer.echo(f'Sprint {created["number"]} criada.')
        return created['id']
    return latest['id']


@app.command()
def create(
    title: str = typer.Argument(..., help='Título do card.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    description: str = typer.Option('', help='Descrição.'),
    sprint: int | None = typer.Option(None, help='Número da sprint. Sem ele, pergunta se quer criar uma nova.'),
    no_input: bool = typer.Option(False, '--no-input', help='Não pergunta nada: usa a última sprint aberta.'),
):
    """Cria um card no Backlog do projeto."""
    owner = find_project(project)
    body = {'title': title, 'description': description}
    sprint_id = choose_sprint(owner, sprint, no_input)
    if sprint_id is not None:
        body['sprint_id'] = sprint_id
    card = request('POST', f'/projects/{owner["id"]}/cards', json=body).json()
    where = f'Sprint {card["sprint"]["number"]}' if card.get('sprint') else 'Backlog'
    typer.echo(f'Card #{card["number"]} {card["title"]} criado em {owner["name"]} ({where}).')


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
    """Inicia o card: move para Em desenvolvimento e abre o cronômetro."""
    card = find_card(project, number)
    started = request('POST', f'/cards/{card["id"]}/start').json()
    if request('POST', f'/cards/{card["id"]}/timer/start', allow=(400,)).status_code == 400:
        typer.echo('Aviso: o cronômetro já estava aberto.')
    where = column_label(started['column'])
    typer.echo(f'Card #{started["number"]} {started["title"]} em {where}, cronômetro rodando.')


@app.command()
def stop(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Para o cronômetro do card e mostra a duração da sessão e o total."""
    card = find_card(project, number)
    response = request('POST', f'/cards/{card["id"]}/timer/stop', allow=(400,))
    if response.status_code == 400:
        fail(f'Não há cronômetro aberto no card #{card["number"]}. Abra um com: hubflow card start {number}')
    total = request('GET', f'/cards/{card["id"]}/time').json()['total_hours']
    session = format_hours(response.json()['hours'])
    typer.echo(f'Cronômetro parado no card #{card["number"]}: sessão de {session}, total {format_hours(total)}.')


@app.command()
def log(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    hours: float = typer.Option(..., help='Horas trabalhadas, por exemplo 1.5.'),
    date: str = typer.Option('', help='Dia do trabalho no formato AAAA-MM-DD (padrão: hoje).'),
    note: str = typer.Option('', help='Observação.'),
):
    """Lança horas manualmente no card."""
    if hours <= 0:
        raise typer.BadParameter('As horas precisam ser maiores que zero.')
    day = parse_iso_date(date) or datetime.date.today().isoformat()
    card = find_card(project, number)
    body = {'hours': hours, 'date': day, 'note': note}
    entry = request('POST', f'/cards/{card["id"]}/time-entries', json=body).json()
    shown = datetime.date.fromisoformat(day).strftime('%d/%m/%Y')
    typer.echo(f'{format_hours(entry["hours"])} lançadas no card #{card["number"]} em {shown}.')


def local_time(value):
    return datetime.datetime.fromisoformat(value).astimezone()


def describe_entry(entry):
    """Linha de uma entrada: data, início–fim, duração, "manual", nota e usuário; "(rodando)" quando aberta."""
    start = local_time(entry['started_at'])
    end = local_time(entry['ended_at']).strftime('%H:%M') if entry['ended_at'] else '...'
    parts = [start.strftime('%d/%m/%Y'), f'{start.strftime("%H:%M")}–{end}', format_hours(entry['hours'])]
    if entry['is_running']:
        parts.append('(rodando)')
    if entry['is_manual']:
        parts.append('manual')
    if entry['note']:
        parts.append(entry['note'])
    parts.append(entry['user']['email'])
    return '  '.join(parts)


@app.command()
def time(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Lista o tempo registrado no card."""
    card = find_card(project, number)
    data = request('GET', f'/cards/{card["id"]}/time').json()
    if not data['entries']:
        typer.echo(f'Nenhum tempo registrado no card #{card["number"]}.')
        return
    for entry in data['entries']:
        typer.echo(describe_entry(entry))
    typer.echo(f'Total: {format_hours(data["total_hours"])}')


def update_card(card_id, **changes):
    """PUT com os campos editáveis do card (a API não tem PATCH), aplicando só as mudanças."""
    card = request('GET', f'/cards/{card_id}').json()
    body = {
        'title': card['title'],
        'description': card['description'],
        'due_date': card['due_date'],
        'assignee_id': card['assignee']['id'] if card['assignee'] else None,
    } | changes
    return request('PUT', f'/cards/{card_id}', json=body).json()


def parse_names(value):
    return [name.strip() for name in value.split(',') if name.strip()]


@app.command()
def comment(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    text: str = typer.Argument(..., help='Texto do comentário (use @email para mencionar).'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Comenta no card."""
    card = find_card(project, number)
    request('POST', f'/cards/{card["id"]}/comments', json={'text': text})
    typer.echo(f'Comentário adicionado ao card #{card["number"]}.')


@app.command()
def label(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    add: str = typer.Option('', help='Etiquetas a adicionar, separadas por vírgula.'),
    remove: str = typer.Option('', help='Etiquetas a remover, separadas por vírgula.'),
):
    """Adiciona ou remove etiquetas do card (pelo nome)."""
    owner = find_project(project)
    by_name = {lb['name'].lower(): lb for lb in request('GET', f'/projects/{owner["id"]}/labels').json()}
    unknown = [n for n in parse_names(add) + parse_names(remove) if n.lower() not in by_name]
    if unknown:
        fail(f'Etiqueta não existe: {", ".join(unknown)}. Etiquetas do projeto: {", ".join(sorted(by_name))}')
    card = find_card(project, number)
    current = {lb['id'] for lb in request('GET', f'/cards/{card["id"]}').json()['labels']}
    current |= {by_name[n.lower()]['id'] for n in parse_names(add)}
    current -= {by_name[n.lower()]['id'] for n in parse_names(remove)}
    updated = request('PUT', f'/cards/{card["id"]}/labels', json={'label_ids': sorted(current)}).json()
    names = ', '.join(lb['name'] for lb in updated['labels']) or 'nenhuma'
    typer.echo(f'Etiquetas do card #{updated["number"]}: {names}')


@app.command()
def assign(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    to: str = typer.Option('', help='E-mail do responsável.'),
    clear: bool = typer.Option(False, '--clear', help='Deixa o card sem responsável.'),
):
    """Define o responsável pelo card."""
    if not to and not clear:
        raise typer.BadParameter('Informe --to EMAIL ou --clear.')
    assignee = None
    if to:
        assignee = next((u for u in request('GET', '/users').json() if u['email'].lower() == to.lower()), None)
        if assignee is None:
            fail(f'Usuário "{to}" não encontrado. Veja os usuários com: hubflow users')
    card = find_card(project, number)
    updated = update_card(card['id'], assignee_id=assignee['id'] if assignee else None)
    who = updated['assignee']['name'] or updated['assignee']['email'] if updated['assignee'] else 'ninguém'
    typer.echo(f'Responsável pelo card #{updated["number"]}: {who}')


@app.command()
def due(
    number: int = typer.Argument(..., help='Número do card no projeto.'),
    date: str = typer.Argument(..., help='Prazo no formato AAAA-MM-DD, ou "nenhum" para limpar.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
):
    """Define o prazo do card."""
    due_date = None if date.lower() in ('nenhum', 'none', '-') else parse_iso_date(date)
    card = find_card(project, number)
    updated = update_card(card['id'], due_date=due_date)
    shown = datetime.date.fromisoformat(updated['due_date']).strftime('%d/%m/%Y') if updated['due_date'] else 'nenhum'
    typer.echo(f'Prazo do card #{updated["number"]}: {shown}')
