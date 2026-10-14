"""Modelos abstratos compartilhados pelas apps (campos de auditoria e ativação)."""

from django.conf import settings
from django.db import models


class CreatedModel(models.Model):
    created = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        abstract = True


class TimeStampedModel(CreatedModel):
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
