from django.conf import settings
from django.db import models

from hubflow.clients.models import Client
from hubflow.core.models import TimeStampedModel

from .catalog import PERMISSIONS


class Access(models.Model):
    """Modelo sem tabela: só existe para registrar as permissões do catálogo no auth do Django."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [(codename, label) for codename, label in PERMISSIONS.items()]


class Membership(TimeStampedModel):
    """Pessoa vinculada a um cliente: define o que é "seu" para quem não vê todos os clientes."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='memberships', verbose_name='cliente')

    class Meta:
        ordering = ('client__name',)
        verbose_name = 'vínculo com cliente'
        verbose_name_plural = 'vínculos com clientes'
        constraints = [models.UniqueConstraint(fields=['user', 'client'], name='unique_membership')]

    def __str__(self):
        return f'{self.user} em {self.client}'
