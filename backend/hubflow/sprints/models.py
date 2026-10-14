from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from hubflow.projects.models import Project


class Milestone(models.Model):
    """Marco opcional do projeto; pode espelhar um milestone do repositório (RN-60)."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones', verbose_name='projeto')
    title = models.CharField('título', max_length=120)
    external_number = models.PositiveIntegerField('número no repositório', null=True, blank=True)
    is_open = models.BooleanField('aberto', default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-id',)
        verbose_name = 'milestone'
        verbose_name_plural = 'milestones'
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'external_number'],
                name='unique_milestone_external_number_per_project',
                nulls_distinct=True,
            )
        ]

    def __str__(self):
        return self.title


class SprintManager(models.Manager):
    def latest_open(self, project):
        return self.filter(project=project, is_open=True).order_by('-number').first()


class Sprint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints', verbose_name='projeto')
    number = models.PositiveIntegerField('número', editable=False)  # RN-60
    name = models.CharField('nome', max_length=120, blank=True)
    milestone = models.ForeignKey(
        Milestone, null=True, blank=True, on_delete=models.SET_NULL, related_name='sprints', verbose_name='milestone'
    )
    start_date = models.DateField('início', null=True, blank=True)
    end_date = models.DateField('fim', null=True, blank=True)
    is_open = models.BooleanField('aberta', default=True)
    closed_at = models.DateTimeField('fechada em', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = SprintManager()

    class Meta:
        ordering = ('project', '-number')
        verbose_name = 'sprint'
        verbose_name_plural = 'sprints'
        constraints = [models.UniqueConstraint(fields=['project', 'number'], name='unique_sprint_number_per_project')]

    def __str__(self):
        return f'Sprint {self.number} · {self.name}' if self.name else f'Sprint {self.number}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'O fim não pode ser antes do início.'})

    def save(self, *args, **kwargs):
        if self._state.adding and self.number is None:
            with transaction.atomic():
                project = Project.objects.select_for_update().get(id=self.project_id)
                project.last_sprint_number += 1
                project.save(update_fields=['last_sprint_number'])
                self.number = project.last_sprint_number
                return super().save(*args, **kwargs)
        super().save(*args, **kwargs)

    def close(self):
        # RN-62: fechar não mexe nos cards.
        self.is_open = False
        self.closed_at = timezone.now()
        self.save(update_fields=['is_open', 'closed_at'])
