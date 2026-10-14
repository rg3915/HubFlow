import re
import subprocess
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command
from django.test import Client as HttpClient

from hubflow.accounts.models import Token

pytestmark = pytest.mark.django_db

FILENAME = re.compile(r'^hubflow-\d{4}-\d{2}-\d{2}-\d{4}\.sql$')


@pytest.fixture
def pg_dump(monkeypatch, settings, tmp_path):
    """pg_dump simulado: guarda a chamada e escreve o arquivo pedido em -f."""
    settings.BASE_DIR = tmp_path
    fake_db = {'HOST': 'db', 'PORT': 5433, 'USER': 'hub', 'PASSWORD': 's3gredo', 'NAME': 'hubflow'}
    for key, value in fake_db.items():  # setitem restaura no fim sem disparar o aviso de troca de DATABASES
        monkeypatch.setitem(settings.DATABASES['default'], key, value)
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[command.index('-f') + 1]).write_text('-- dump')
        return subprocess.CompletedProcess(command, 0, '', '')

    monkeypatch.setattr(subprocess, 'run', fake_run)
    return calls


@pytest.fixture
def root(user):
    user.is_superuser = True
    user.save()
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=user).key}'})


def test_command_roda_pg_dump_e_grava_em_backups(pg_dump, tmp_path):
    call_command('backup_db')

    command, kwargs = pg_dump[0]
    path = Path(command[-1])
    assert command[:-1] == ['pg_dump', '-h', 'db', '-p', '5433', '-U', 'hub', '-d', 'hubflow', '-f']
    assert kwargs['env']['PGPASSWORD'] == 's3gredo'
    assert path.parent == tmp_path / 'backups'
    assert FILENAME.match(path.name)
    assert path.read_text() == '-- dump'


def test_command_aceita_output(pg_dump, tmp_path):
    call_command('backup_db', output=str(tmp_path / 'outra'))

    path = Path(pg_dump[0][0][-1])
    assert path.parent == tmp_path / 'outra'
    assert path.exists()


def test_command_sem_pg_dump_da_erro_claro(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, 'run', missing)

    with pytest.raises(CommandError, match='pg_dump'):
        call_command('backup_db')


def test_post_gera_backup(root, pg_dump):
    response = root.post('/api/backups')

    assert response.status_code == 201
    assert FILENAME.match(response.json()['filename'])
    assert response.json()['size'] == len('-- dump')
    assert len(pg_dump) == 1


def test_post_sem_pg_dump_retorna_400(root, monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, 'run', missing)

    response = root.post('/api/backups')

    assert response.status_code == 400
    assert 'pg_dump' in response.json()['detail']


def test_usuario_comum_recebe_403(api, pg_dump):
    assert api.post('/api/backups').status_code == 403
    assert api.get('/api/backups').status_code == 403
    assert pg_dump == []


def test_get_lista_backups(root, settings, tmp_path):
    settings.BASE_DIR = tmp_path
    (tmp_path / 'backups').mkdir()
    (tmp_path / 'backups' / 'hubflow-2026-01-02-0300.sql').write_text('a')
    (tmp_path / 'backups' / 'hubflow-2026-01-01-0300.sql').write_text('bb')
    (tmp_path / 'backups' / 'notas.txt').write_text('x')

    response = root.get('/api/backups')

    assert response.status_code == 200
    assert response.json() == [
        {'filename': 'hubflow-2026-01-02-0300.sql', 'size': 1},
        {'filename': 'hubflow-2026-01-01-0300.sql', 'size': 2},
    ]


def test_get_sem_pasta_devolve_lista_vazia(root, settings, tmp_path):
    settings.BASE_DIR = tmp_path

    assert root.get('/api/backups').json() == []
