import typer

from .cards import Column, column_label
from .client import fail, request
from .projects import find_project

app = typer.Typer(help='Automações do projeto: quando <gatilho> → <ação>.', no_args_is_help=True)

WHEN_HELP = 'created | entered:COLUNA | sla | sla:COLUNA'
THEN_HELP = 'move:COLUNA | assign:EMAIL | label:NOME | notify'
FIELDS = ['name', 'is_active', 'trigger', 'trigger_column', 'action', 'action_column']
FIELDS += ['action_user_id', 'action_label_id']


def column_arg(value, usage):
    if value not in Column.__members__:
        names = ', '.join(Column.__members__)
        raise typer.BadParameter(f'Coluna "{value}" não existe. Use {usage} com uma de: {names}.')
    return value


def parse_when(value):
    kind, _, column = value.partition(':')
    if kind == 'created' and not column:
        return {'trigger': 'created', 'trigger_column': ''}
    if kind == 'entered' and column:
        return {'trigger': 'entered_column', 'trigger_column': column_arg(column, '--when entered:COLUNA')}
    if kind == 'sla':
        return {'trigger': 'sla_breached', 'trigger_column': column_arg(column, '--when sla:COLUNA') if column else ''}
    raise typer.BadParameter(f'Use --when {WHEN_HELP}.')


def parse_then(value, project):
    kind, _, arg = value.partition(':')
    action = {'action': kind, 'action_column': '', 'action_user_id': None, 'action_label_id': None}
    if kind == 'move' and arg:
        action['action_column'] = column_arg(arg, '--then move:COLUNA')
    elif kind == 'assign' and arg:
        users = request('GET', '/users').json()
        user = next((u for u in users if u['email'].lower() == arg.lower()), None)
        action['action_user_id'] = (user or fail(f'Pessoa "{arg}" não encontrada.'))['id']
    elif kind == 'label' and arg:
        labels = request('GET', f'/projects/{project["id"]}/labels').json()
        label = next((lb for lb in labels if lb['name'].lower() == arg.lower()), None)
        action['action_label_id'] = (label or fail(f'Etiqueta "{arg}" não existe em {project["name"]}.'))['id']
    elif kind != 'notify' or arg:
        raise typer.BadParameter(f'Use --then {THEN_HELP}.')
    return action


def project_rules(project):
    return request('GET', f'/projects/{project["id"]}/automations').json()


@app.command('list')
def list_rules(project: str = typer.Option(..., help='Nome do projeto.')):
    """Lista as automações do projeto."""
    rules = project_rules(find_project(project))
    if not rules:
        typer.echo(f'Nenhuma automação. Crie com: hubflow automation add NOME --project {project} --when … --then …')
    for rule in rules:
        state = 'ligada' if rule['is_active'] else 'desligada'
        typer.echo(f'#{rule["id"]}  {state}  {rule["name"]}: {rule["description"]}')


@app.command()
def add(
    name: str = typer.Argument(..., help='Nome da automação.'),
    project: str = typer.Option(..., help='Nome do projeto.'),
    when: str = typer.Option(..., help=WHEN_HELP),
    then: str = typer.Option(..., help=THEN_HELP),
):
    """Cria uma automação. Ex.: --when entered:qa --then move:done"""
    owner = find_project(project)
    body = {'name': name, 'is_active': True} | parse_when(when) | parse_then(then, owner)
    rule = request('POST', f'/projects/{owner["id"]}/automations', json=body).json()
    typer.echo(f'Automação #{rule["id"]} criada: {rule["description"]}')


@app.command()
def toggle(rule_id: int = typer.Argument(..., help='Número da automação.'), project: str = typer.Option(...)):
    """Liga ou desliga uma automação."""
    rule = next((r for r in project_rules(find_project(project)) if r['id'] == rule_id), None)
    if rule is None:
        fail(f'Automação #{rule_id} não existe em {project}. Veja com: hubflow automation list --project {project}')
    body = {field: rule[field] for field in FIELDS} | {'is_active': not rule['is_active']}
    rule = request('PUT', f'/automations/{rule_id}', json=body).json()
    typer.echo(f'Automação #{rule_id} {"ligada" if rule["is_active"] else "desligada"}.')


@app.command()
def remove(rule_id: int = typer.Argument(..., help='Número da automação.')):
    """Exclui uma automação."""
    request('DELETE', f'/automations/{rule_id}')
    typer.echo(f'Automação #{rule_id} excluída.')


def sla(
    name: str = typer.Argument(..., help='Nome do projeto.'),
    column: Column | None = typer.Option(None, help='Coluna para definir o SLA.'),
    hours: int | None = typer.Option(None, min=1, help='Horas máximas na coluna.'),
    clear: bool = typer.Option(False, '--clear', help='Tira o SLA da coluna.'),
):
    """Mostra o SLA por coluna; com --column e --hours (ou --clear), altera."""
    owner = find_project(name)
    if column:
        if hours is None and not clear:
            raise typer.BadParameter('Informe --hours N ou --clear.')
        slas = request('PUT', f'/projects/{owner["id"]}/sla', json={column.value: None if clear else hours}).json()
    else:
        slas = request('GET', f'/projects/{owner["id"]}/sla').json()
    for key, value in slas.items():
        typer.echo(f'{column_label(key)}: {f"{value}h" if value else "—"}')
