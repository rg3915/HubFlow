from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models


def validate_email_list(value):
    # RN-12: lista opcional com um ou mais endereços válidos.
    if not isinstance(value, list):
        raise ValidationError('Informe uma lista de e-mails.')
    for email in value:
        validate_email(email)


class Client(models.Model):
    name = models.CharField('nome', max_length=120, unique=True)  # RN-10
    emails = models.JSONField('e-mails de notificação', default=list, blank=True, validators=[validate_email_list])
    is_active = models.BooleanField('ativo', default=True)
    created = models.DateTimeField('criado em', auto_now_add=True)
    modified = models.DateTimeField('modificado em', auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'

    def __str__(self):
        return self.name
