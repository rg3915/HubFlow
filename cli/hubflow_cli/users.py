import typer

from .client import fail, find_by_name, request

app = typer.Typer(help='Pessoas, papéis e permissões (só quem gerencia usuários).', no_args_is_help=True)


def find_person(email):
    for person in request('GET', '/users/manage').json():
        if person['email'].lower() == email.lower():
            return person
    fail(f'Pessoa "{email}" não encontrada. Veja com: hubflow user list')


@app.command('list')
def list_users():
    """Lista as pessoas com papéis, clientes e situação."""
    for person in request('GET', '/users/manage').json():
        roles = 'superusuário' if person['is_superuser'] else ', '.join(person['roles']) or 'sem papel'
        clients = ', '.join(c['name'] for c in person['clients'])
        name = f'  {person["name"]}' if person['name'] else ''
        status = '' if person['is_active'] else '  (inativo)'
        typer.echo(f'{person["email"]}{name}  [{roles}]{"  " + clients if clients else ""}{status}')


@app.command()
def invite(
    email: str = typer.Argument(..., help='E-mail da pessoa.'),
    name: str = typer.Option('', help='Nome.'),
    role: list[str] = typer.Option([], help='Papel (repita para mais de um), ex.: Desenvolvedor.'),
    client: list[str] = typer.Option([], help='Cliente vinculado, pelo nome (repita para mais de um).'),
):
    """Convida uma pessoa: ela recebe o link para definir a senha."""
    client_ids = [find_by_name('/clients', n, 'Cliente', 'hubflow client list')['id'] for n in client]
    payload = {'email': email, 'name': name, 'roles': role, 'client_ids': client_ids}
    request('POST', '/users/invite', json=payload)
    typer.echo(f'Convite enviado para {email}.')


@app.command('role')
def set_role(
    email: str = typer.Argument(..., help='E-mail da pessoa.'),
    roles: list[str] = typer.Option(..., '--set', help='Papel (repita para mais de um); substitui os atuais.'),
):
    """Define os papéis da pessoa."""
    person = request('PUT', f'/users/{find_person(email)["id"]}/roles', json={'roles': roles}).json()
    typer.echo(f'{person["email"]}: {", ".join(person["roles"]) or "sem papel"}')


@app.command()
def grant(
    email: str = typer.Argument(..., help='E-mail da pessoa.'),
    perm: str = typer.Option(..., help='Permissão, ex.: billing.view_payment.'),
    revoke: bool = typer.Option(False, '--revoke', help='Remove a permissão em vez de dar.'),
):
    """Dá (ou, com --revoke, tira) uma permissão por pessoa, além das do papel."""
    person = find_person(email)
    extra = [p for p in person['extra_permissions'] if p != perm] + ([] if revoke else [perm])
    person = request('PUT', f'/users/{person["id"]}/permissions', json={'permissions': extra}).json()
    typer.echo(f'{person["email"]}: {", ".join(person["extra_permissions"]) or "sem permissões por pessoa"}')
