from django.core.management.base import BaseCommand

from hubflow.reports.services import send_due_reports


class Command(BaseCommand):
    help = 'Envia os relatórios agendados dos períodos já encerrados (rodar junto do check_sla).'

    def handle(self, *args, **options):
        self.stdout.write(f'Relatórios enviados: {send_due_reports()}')
