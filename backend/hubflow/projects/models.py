from django.db import models

from hubflow.clients.models import Client, validate_email_list
from hubflow.core.models import ActiveModel, TimeStampedModel, UuidModel


class Project(UuidModel, TimeStampedModel, ActiveModel):
    class Provider(models.TextChoices):
        GITHUB = 'github', 'GitHub'
        GITLAB = 'gitlab', 'GitLab'

    PROVIDER_HOSTS = {Provider.GITHUB: 'https://github.com', Provider.GITLAB: 'https://gitlab.com'}

    # RN-11: cliente com projetos não pode ser excluído.
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='projects', verbose_name='cliente')
    name = models.CharField('nome', max_length=120)
    provider = models.CharField('provedor', max_length=10, choices=Provider.choices)
    owner = models.CharField(max_length=120)
    repo = models.CharField('repositório', max_length=120)
    description = models.TextField('descrição', blank=True)
    emails = models.JSONField('e-mails de notificação', default=list, blank=True, validators=[validate_email_list])
    # RN-41: cada evento de notificação pode ser ligado/desligado por projeto.
    notify_on_created = models.BooleanField('avisar card criado', default=True)
    notify_on_moved = models.BooleanField('avisar card movido', default=True)
    notify_on_done = models.BooleanField('avisar card concluído', default=True)
    # Integração com o repositório (nunca exposto pela API).
    repo_token = models.CharField('token do repositório', max_length=200, blank=True)
    gitlab_project_id = models.PositiveIntegerField('id do projeto no GitLab', null=True, blank=True)
    create_issues = models.BooleanField('criar issue no repositório ao criar card', default=False)
    webhook_secret = models.CharField('segredo do webhook', max_length=100, blank=True)
    # RN-32: contador dos números de card; nunca volta, mesmo quando um card é excluído.
    last_card_number = models.PositiveIntegerField(default=0, editable=False)
    # RN-60: contador das sprints, nunca volta.
    last_sprint_number = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ('client__name', 'name')
        verbose_name = 'projeto'
        verbose_name_plural = 'projetos'
        constraints = [
            # RN-21
            models.UniqueConstraint(fields=['client', 'name'], name='unique_project_name_per_client'),
            # RN-22
            models.UniqueConstraint(fields=['provider', 'owner', 'repo'], name='unique_repository'),
        ]

    def __str__(self):
        return f'{self.client} / {self.name}'

    @property
    def repository_url(self):
        return f'{self.PROVIDER_HOSTS[self.provider]}/{self.owner}/{self.repo}'

    @property
    def notification_emails(self):
        # RN-23: sem e-mails no projeto, valem os do cliente.
        return self.emails or self.client.emails
