from datetime import date

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


class Label(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels', verbose_name='projeto')
    name = models.CharField('nome', max_length=40)
    color = models.CharField('cor', max_length=7, default='#64748b')  # hex #rrggbb

    class Meta:
        ordering = ('name',)
        verbose_name = 'etiqueta'
        verbose_name_plural = 'etiquetas'

    def __str__(self):
        return self.name


class Card(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cards', verbose_name='projeto')
    number = models.PositiveIntegerField('número', editable=False)  # RN-32
    title = models.CharField('título', max_length=200)  # RN-38
    description = models.TextField('descrição', blank=True)
    column = models.CharField('coluna', max_length=10, choices=Column.choices, default=Column.BACKLOG)
    position = models.PositiveIntegerField('posição', default=0)  # RN-33
    labels = models.ManyToManyField(Label, blank=True, related_name='cards', verbose_name='etiquetas')
    due_date = models.DateField('prazo', null=True, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_cards',
        verbose_name='responsável',
    )
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

    @property
    def is_overdue(self):
        # Vencido = prazo no passado e ainda não concluído/arquivado.
        open_columns = (Column.DONE, Column.ARCHIVED)
        return bool(self.due_date and self.due_date < date.today() and self.column not in open_columns)

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


class CardMove(models.Model):
    # RN-35: histórico de movimentações entre colunas.
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='moves')
    from_column = models.CharField(max_length=10, choices=Column.choices)
    to_column = models.CharField(max_length=10, choices=Column.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created', '-id')

    def __str__(self):
        return f'{self.card} {self.from_column} → {self.to_column}'


class Comment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField('texto')
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='+')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created', 'id')
        verbose_name = 'comentário'
        verbose_name_plural = 'comentários'

    def __str__(self):
        return f'{self.author} em {self.card}: {self.text[:40]}'


class ChecklistItem(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='checklist_items')
    text = models.CharField('texto', max_length=200)
    done = models.BooleanField('feito', default=False)
    position = models.PositiveIntegerField('posição', default=0)

    class Meta:
        ordering = ('position', 'id')
        verbose_name = 'item de checklist'
        verbose_name_plural = 'itens de checklist'

    def __str__(self):
        return self.text
