from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from hubflow.boards.models import Column, Label
from hubflow.core.models import ActiveModel, CreatedByModel, TimeStampedModel, UuidModel
from hubflow.projects.models import Project


class Automation(UuidModel, TimeStampedModel, CreatedByModel, ActiveModel):
    """Regra do projeto: quando <gatilho> → <ação> (RN-110)."""

    TRIGGERS = {
        'created': 'Quando um card for criado',
        'entered_column': 'Quando o card entrar em',
        'sla_breached': 'Quando o SLA estourar',
    }
    ACTIONS = {
        'move': 'mover para',
        'assign': 'definir responsável',
        'add_label': 'adicionar etiqueta',
        'notify': 'avisar quem criou e o responsável',
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='automations')
    name = models.CharField('nome', max_length=100)
    trigger = models.CharField('gatilho', max_length=20, choices=TRIGGERS)
    trigger_column = models.CharField('coluna do gatilho', max_length=10, choices=Column.choices, blank=True)
    action = models.CharField('ação', max_length=20, choices=ACTIONS)
    action_column = models.CharField('coluna de destino', max_length=10, choices=Column.choices, blank=True)
    action_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='responsável',
    )
    action_label = models.ForeignKey(
        Label, null=True, blank=True, on_delete=models.CASCADE, related_name='+', verbose_name='etiqueta'
    )

    class Meta:
        ordering = ('created', 'id')
        verbose_name = 'automação'
        verbose_name_plural = 'automações'

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.trigger == 'entered_column' and not self.trigger_column:
            errors['trigger_column'] = 'Escolha a coluna do gatilho.'
        if self.action == 'move':
            if not self.action_column:
                errors['action_column'] = 'Escolha a coluna de destino.'
            elif self.trigger == 'entered_column' and self.action_column == self.trigger_column:
                errors['action_column'] = 'Mover para a mesma coluna do gatilho não faz nada.'
        if self.action == 'assign' and not self.action_user_id:
            errors['action_user'] = 'Escolha o responsável.'
        if self.action == 'add_label':
            if not self.action_label_id:
                errors['action_label'] = 'Escolha a etiqueta.'
            elif self.action_label.project_id != self.project_id:
                errors['action_label'] = 'Use uma etiqueta deste projeto.'
        if errors:
            raise ValidationError(errors)

    def describe(self):
        when = self.TRIGGERS[self.trigger]
        if self.trigger == 'entered_column':
            when = f'Quando o card entrar em {Column(self.trigger_column).label}'
        then = {
            'move': lambda: f'mover para {Column(self.action_column).label}',
            'assign': lambda: f'definir {self.action_user.first_name} como responsável',
            'add_label': lambda: f'adicionar a etiqueta {self.action_label.name}',
            'notify': lambda: self.ACTIONS['notify'],
        }[self.action]()
        return f'{when} → {then}'
