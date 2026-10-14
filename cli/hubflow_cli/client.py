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
