from django.core.management.base import BaseCommand

from hubflow.automations.services import check_deadlines_and_sla


class Command(BaseCommand):
    help = 'Dispara os SLAs estourados e avisa os prazos vencidos (rodar a cada 15 minutos).'

    def handle(self, *args, **options):
        result = check_deadlines_and_sla()
        self.stdout.write(f'SLA estourado: {result["sla"]} · prazos vencidos avisados: {result["overdue"]}')
