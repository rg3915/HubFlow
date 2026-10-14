import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config

BACKUP = {'filename': 'hubflow-2026-10-14-0930.sql', 'size': 2048}


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})


@respx.mock
def test_backup_gera_e_mostra_o_arquivo(run):
    route = respx.post('http://api.test/api/backups').mock(return_value=Response(201, json=BACKUP))

    result = run('backup')

    assert result.exit_code == 0, result.output
    assert route.called
    assert 'hubflow-2026-10-14-0930.sql' in result.output


@respx.mock
def test_backup_list_mostra_os_arquivos(run):
    older = {'filename': 'hubflow-2026-10-13-0930.sql', 'size': 1024}
    respx.get('http://api.test/api/backups').mock(return_value=Response(200, json=[BACKUP, older]))

    result = run('backup', '--list')

    assert result.exit_code == 0, result.output
    assert 'hubflow-2026-10-14-0930.sql' in result.output
    assert 'hubflow-2026-10-13-0930.sql' in result.output


@respx.mock
def test_backup_list_vazia(run):
    respx.get('http://api.test/api/backups').mock(return_value=Response(200, json=[]))

    result = run('backup', '--list')

    assert result.exit_code == 0, result.output
    assert 'Nenhum backup' in result.output


@respx.mock
def test_backup_sem_permissao_falha(run):
    detail = {'detail': 'Só superusuários mexem nos backups.'}
    respx.post('http://api.test/api/backups').mock(return_value=Response(403, json=detail))

    result = run('backup')

    assert result.exit_code == 1
    assert 'superusuários' in result.output
