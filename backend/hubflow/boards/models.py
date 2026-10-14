from django.conf import settings
from django.db import models, transaction
from django.db.models import Max

from hubflow.projects.models import Project


class Column(models.TextChoices):
    # RN-30: colunas fixas, nesta ordem.
    BACKLOG = 'backlog', 'Backlog'
    SPRINT = 'sprint', 'Sprint'
    DOING = 'doing', 'Em desenvolvimento'
    QA = 'qa', 'QA'
    DONE = 'done', 'Concluído'
    ARCHIVED = 'archived', 'Arquivadas'


class Card(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cards', verbose_name='projeto')
    number = models.PositiveIntegerField('número', editable=False)  # RN-32
    title = models.CharField('título', max_length=200)  # RN-38
    description = models.TextField('descrição', blank=True)
    column = models.CharField('coluna', max_length=10, choices=Column.choices, default=Column.BACKLOG)
    position = models.PositiveIntegerField('posição', default=0)  # RN-33
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    created = models.DateTimeField('criado em', auto_now_add=True)
    modified = models.DateTimeField('modificado em', auto_now=True)

    class Meta:
        ordering = ('project', 'column', 'position')
        verbose_name = 'card'
        verbose_name_plural = 'cards'
        constraints = [models.UniqueConstraint(fields=['project', 'number'], name='unique_card_number_per_project')]

    def __str__(self):
        return f'#{self.number} {self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            with transaction.atomic():
                # Trava o projeto para dois cards criados ao mesmo tempo não disputarem o número.
                project = Project.objects.select_for_update().get(id=self.project_id)
                siblings = Card.objects.filter(project_id=self.project_id)
                if self.number is None:
                    project.last_card_number += 1
                    project.save(update_fields=['last_card_number'])
                    self.number = project.last_card_number
                # RN-31: entra na última posição da coluna.
                last = siblings.filter(column=self.column).aggregate(last=Max('position'))['last']
                self.position = 0 if last is None else last + 1
                return super().save(*args, **kwargs)
        super().save(*args, **kwargs)
