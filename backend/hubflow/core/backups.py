"""Backup .sql do banco via pg_dump; usado pelo command `backup_db` e por POST /api/backups."""

import os
import subprocess

from django.conf import settings
from django.utils import timezone


class BackupError(Exception):
    pass


def backup_dir():
    return settings.BASE_DIR / 'backups'


def run_backup(output=None):
    """Roda o pg_dump do banco `default` e devolve o Path do .sql gerado."""
    db = settings.DATABASES['default']
    folder = output or backup_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'hubflow-{timezone.localtime():%Y-%m-%d-%H%M}.sql'
    command = ['pg_dump']
    for flag, key in (('-h', 'HOST'), ('-p', 'PORT'), ('-U', 'USER'), ('-d', 'NAME')):
        if db.get(key):
            command += [flag, str(db[key])]
    command += ['-f', str(path)]
    env = os.environ | {'PGPASSWORD': db.get('PASSWORD') or ''}
    try:
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise BackupError('pg_dump não encontrado. Instale o cliente do PostgreSQL (postgresql-client).')
    except subprocess.CalledProcessError as error:
        raise BackupError(f'pg_dump falhou: {error.stderr.strip()}')
    return path


def describe(path):
    return {'filename': path.name, 'size': path.stat().st_size}


def list_backups():
    """Arquivos .sql da pasta de backups, do mais novo ao mais antigo (o nome carrega a data)."""
    return [describe(path) for path in sorted(backup_dir().glob('*.sql'), reverse=True)]
