import httpx
import typer

from . import config


def fail(message):
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def request(method, path, *, auth=True, **kwargs):
    url = config.api_url()
    headers = {}
    if auth:
        key = config.token()
        if not key:
            fail('Você não está logado. Rode: hubflow login')
        headers['Authorization'] = f'Bearer {key}'
    try:
        response = httpx.request(method, f'{url}/api{path}', headers=headers, **kwargs)
    except httpx.HTTPError, ConnectionError:
        fail(f'Não foi possível conectar à API em {url}.')
    if response.status_code >= 500:
        fail(f'Erro interno da API ({response.status_code}).')
    if response.status_code >= 400:
        try:
            detail = response.json().get('detail', response.text)
        except ValueError:
            detail = response.text
        fail(f'Erro {response.status_code}: {detail}')
    return response


def find_by_name(path, name, label, hint):
    """Devolve o registro de `path` cujo nome bate (sem diferenciar maiúsculas) ou encerra com dica."""
    for item in request('GET', path).json():
        if item['name'].lower() == name.lower():
            return item
    fail(f'{label} "{name}" não encontrado. Veja os nomes com: {hint}')


def parse_iso_date(value):
    """AAAA-MM-DD → string ISO; None quando vazio. Erro de uso amigável para o resto."""
    import datetime

    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except ValueError:
        raise typer.BadParameter(f'Use o formato AAAA-MM-DD, por exemplo {datetime.date.today().isoformat()}.')
