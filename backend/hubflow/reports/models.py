from django.db import models

from hubflow.clients.models import Client
from hubflow.core.models import ActiveModel, CreatedByModel, TimeStampedModel, UuidModel
from hubflow.projects.models import Project

from .services import PERIODS


class ReportSchedule(UuidModel, TimeStampedModel, CreatedByModel, ActiveModel):
    """Relatório enviado por e-mail ao fim de cada período, com as permissões de quem criou (RN-121)."""

    client = models.ForeignKey(
        Client, null=True, blank=True, on_delete=models.CASCADE, related_name='report_schedules'
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.CASCADE, related_name='report_schedules'
    )
    frequency = models.CharField('frequência', max_length=10, choices=PERIODS)
    emails = models.JSONField('destinatários', default=list, blank=True)  # vazio = e-mails do projeto/cliente
    last_period_end = models.DateField('último período enviado', null=True, blank=True)

    class Meta:
        ordering = ('created', 'id')
        verbose_name = 'relatório agendado'
        verbose_name_plural = 'relatórios agendados'

    def __str__(self):
        return f'{self.get_frequency_display()} · {self.scope_name}'

    @property
    def scope_name(self):
        return self.project.name if self.project_id else self.client.name
