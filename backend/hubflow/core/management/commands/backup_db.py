"""Gera um backup .sql do banco com pg_dump em backups/hubflow-AAAA-MM-DD-HHMM.sql.

Uso:       uv run manage.py backup_db [--output DIR]
Restaurar (num banco vazio): psql -h HOST -U USUARIO -d hubflow < backups/hubflow-AAAA-MM-DD-HHMM.sql
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from hubflow.core.backups import BackupError, run_backup


class Command(BaseCommand):
    help = 'Gera um backup .sql do banco com pg_dump.'

    def add_arguments(self, parser):
        parser.add_argument('--output', help='Pasta de destino (padrão: backend/backups).')

    def handle(self, *args, output=None, **options):
        try:
            path = run_backup(Path(output) if output else None)
        except BackupError as error:
            raise CommandError(str(error))
        self.stdout.write(f'Backup salvo em {path}')
