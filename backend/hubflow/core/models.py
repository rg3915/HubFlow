"""Modelos abstratos compartilhados pelas apps (campos de auditoria e ativação)."""

import uuid

from django.conf import settings
from django.db import models


class UuidModel(models.Model):
    # uuid7 (ordenável pelo tempo) para identificar o registro fora do banco; a pk inteira continua nas rotas.
    uuid = models.UUIDField('uuid', default=uuid.uuid7, unique=True, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created = models.DateTimeField('criado em', auto_now_add=True)
    modified = models.DateTimeField('modificado em', auto_now=True)

    class Meta:
        abstract = True


class CreatedByModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='criado por',
    )

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    is_active = models.BooleanField('ativo', default=True)

    class Meta:
        abstract = True
