import typer

from .client import fail, request
from .projects import find_project

app = typer.Typer(help='Campos personalizados dos cards de um projeto.', no_args_is_help=True)

KINDS = {'text': 'texto', 'number': 'número', 'date': 'data', 'select': 'seleção', 'bool': 'sim/não'}
YES, NO = {'sim', 's', 'true', '1', 'yes'}, {'não', 'nao', 'n', 'false', '0', 'no'}


def project_fields(project):
    return request('GET', f'/projects/{project["id"]}/fields').json()


def find_field(fields, name, project):
    for field in fields:
        if field['name'].lower() == name.strip().lower():
            return field
    fail(f'Campo "{name}" não existe. Veja com: hubflow project field list {project["name"]}')


def parse_value(field, raw):
    """Texto da linha de comando → valor do tipo do campo; vazio apaga (None)."""
    raw = raw.strip()
    if not raw:
        return None
    if field['kind'] == 'number':
        try:
            number = float(raw.replace(',', '.'))
        except ValueError:
            raise typer.BadParameter(f'{field["name"]}: informe um número.')
        return int(number) if number.is_integer() else number
    if field['kind'] == 'bool':
        if raw.lower() not in YES | NO:
            raise typer.BadParameter(f'{field["name"]}: use sim ou não.')
        return raw.lower() in YES
    return raw


def parse_field_args(project, items):
    """['Prioridade=Alta', ...] → {'id': valor} pronto para a API."""
    if not items:
        return {}
    fields = project_fields(project)
    values = {}
    for item in items:
        name, sep, raw = item.partition('=')
        if not sep:
            raise typer.BadParameter(f'Use o formato Nome=valor, não "{item}".')
        field = find_field(fields, name, project)
        values[str(field['id'])] = parse_value(field, raw)
    return values


def describe(field):
    options = f' ({", ".join(field["options"])})' if field['options'] else ''
    required = '  obrigatório' if field['required'] else ''
    return f'{field["name"]}  {KINDS.get(field["kind"], field["kind"])}{options}{required}'


@app.command('list')
def list_fields(project: str = typer.Argument(..., help='Nome do projeto.')):
    """Lista os campos do projeto."""
    fields = project_fields(find_project(project))
    if not fields:
        typer.echo(f'Nenhum campo. Crie com: hubflow project field add {project} NOME --kind text')
    for field in fields:
        typer.echo(describe(field))


@app.command()
def add(
    project: str = typer.Argument(..., help='Nome do projeto.'),
    name: str = typer.Argument(..., help='Nome do campo.'),
    kind: str = typer.Option('text', help='text, number, date, select ou bool.'),
    option: list[str] = typer.Option([], help='Opção da seleção (repita para cada uma).'),
    required: bool = typer.Option(False, '--required', help='Obrigatório ao criar card.'),
):
    """Cria um campo no projeto."""
    owner = find_project(project)
    body = {'name': name, 'kind': kind, 'options': option, 'required': required}
    field = request('POST', f'/projects/{owner["id"]}/fields', json=body).json()
    typer.echo(f'Campo {field["name"]} criado em {owner["name"]}.')


@app.command()
def remove(
    project: str = typer.Argument(..., help='Nome do projeto.'),
    name: str = typer.Argument(..., help='Nome do campo.'),
):
    """Exclui um campo (os valores dele somem dos cards)."""
    owner = find_project(project)
    field = find_field(project_fields(owner), name, owner)
    request('DELETE', f'/fields/{field["id"]}')
    typer.echo(f'Campo {field["name"]} excluído de {owner["name"]}.')
