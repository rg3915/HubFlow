from django.conf import settings
from django.db import models

from hubflow.clients.models import Client
from hubflow.core.models import CreatedByModel, TimeStampedModel, UuidModel

from .catalog import CUSTOM_PERMISSIONS


class Access(models.Model):
    """Modelo sem tabela: só existe para registrar as permissões específicas (sem equivalente padrão)."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [(codename, label) for codename, label in CUSTOM_PERMISSIONS.items()]


class Membership(UuidModel, TimeStampedModel):
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


class PermissionChange(UuidModel, TimeStampedModel, CreatedByModel):
    """Registro de mudança de papel, permissão, vínculo, situação ou convite: quem fez (created_by), quando e o quê."""

    ACTIONS = {
        'invite': 'Convite',
        'roles': 'Papéis',
        'permissions': 'Permissões por pessoa',
        'clients': 'Clientes vinculados',
        'active': 'Situação',
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permission_changes')
    action = models.CharField('ação', max_length=20, choices=ACTIONS)
    before = models.JSONField('antes', default=list)
    after = models.JSONField('depois', default=list)

    class Meta:
        ordering = ('-created', '-id')
        verbose_name = 'alteração de permissão'
        verbose_name_plural = 'alterações de permissões'

    def __str__(self):
        return f'{self.get_action_display()} de {self.user}'
