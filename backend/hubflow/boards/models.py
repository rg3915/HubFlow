from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.db.models.functions import Lower
from django.utils import timezone

from hubflow.core.models import CreatedByModel, TimeStampedModel, UuidModel
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint


class Column(models.TextChoices):
    # RN-30: colunas fixas, nesta ordem.
    BACKLOG = 'backlog', 'Backlog'
    SPRINT = 'sprint', 'Sprint'
    DOING = 'doing', 'Em desenvolvimento'
    QA = 'qa', 'QA'
    DONE = 'done', 'Concluído'
    ARCHIVED = 'archived', 'Arquivadas'


class Label(UuidModel, TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels', verbose_name='projeto')
    name = models.CharField('nome', max_length=40)
    color = models.CharField('cor', max_length=7, default='#64748b')  # hex #rrggbb

    class Meta:
        ordering = ('name',)
        verbose_name = 'etiqueta'
        verbose_name_plural = 'etiquetas'

    def __str__(self):
        return self.name


class Card(UuidModel, TimeStampedModel, CreatedByModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cards', verbose_name='projeto')
    number = models.PositiveIntegerField('número', editable=False)  # RN-32
    title = models.CharField('título', max_length=200)  # RN-38
    description = models.TextField('descrição', blank=True)
    column = models.CharField('coluna', max_length=10, choices=Column.choices, default=Column.BACKLOG)
    position = models.PositiveIntegerField('posição', default=0)  # RN-33
    labels = models.ManyToManyField(Label, blank=True, related_name='cards', verbose_name='etiquetas')
    # RN-61: todo card pertence a uma sprint (o serviço garante; o banco aceita nulo só para dados antigos).
    sprint = models.ForeignKey(Sprint, null=True, blank=True, on_delete=models.PROTECT, related_name='cards')
    due_date = models.DateField('prazo', null=True, blank=True)
    estimate_hours = models.FloatField('estimativa (horas)', null=True, blank=True)
    custom_values = models.JSONField('campos personalizados', default=dict, blank=True)  # {id do campo: valor}
    column_entered_at = models.DateTimeField('entrou na coluna em', default=timezone.now)  # base do SLA
    sla_breached_at = models.DateTimeField('SLA estourado em', null=True, blank=True)  # zera ao mudar de coluna
    due_notified_on = models.DateField('prazo já avisado', null=True, blank=True)  # avisa de novo se o prazo mudar
    # Issue espelhada no repositório (GitHub: number; GitLab: iid).
    issue_number = models.PositiveIntegerField('número da issue', null=True, blank=True)
    issue_url = models.URLField('URL da issue', blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_cards',
        verbose_name='responsável',
    )

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


class CardMove(UuidModel, TimeStampedModel):
    # RN-35: histórico de movimentações entre colunas.
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='moves')
    from_column = models.CharField(max_length=10, choices=Column.choices)
    to_column = models.CharField(max_length=10, choices=Column.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        ordering = ('-created', '-id')

    def __str__(self):
        return f'{self.card} {self.from_column} → {self.to_column}'


class Comment(UuidModel, TimeStampedModel):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField('texto')
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='+')

    class Meta:
        ordering = ('created', 'id')
        verbose_name = 'comentário'
        verbose_name_plural = 'comentários'

    def __str__(self):
        return f'{self.author} em {self.card}: {self.text[:40]}'


class ChecklistItem(UuidModel, TimeStampedModel):
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


class Attachment(UuidModel, TimeStampedModel):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField('arquivo', upload_to='attachments/%Y/%m/')
    name = models.CharField('nome', max_length=255)
    size = models.PositiveIntegerField('tamanho em bytes')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ('created', 'id')
        verbose_name = 'anexo'
        verbose_name_plural = 'anexos'

    def __str__(self):
        return self.name


class CardEvent(UuidModel, TimeStampedModel):
    """Mudanças no card que não são movimentação, comentário nem anexo (esses têm tabela própria)."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='events')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    kind = models.CharField(max_length=20)  # created, assignee, due_date, labels
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created', '-id')

    def __str__(self):
        return f'{self.card} {self.kind}'


class Notification(UuidModel, TimeStampedModel):
    """Aviso no app (sino): menção, comentário em card seu ou de que é responsável, card seu movido."""

    KINDS = {
        'mention': 'Menção',
        'comment': 'Comentário',
        'moved': 'Card movido',
        'automation': 'Automação',
        'overdue': 'Prazo vencido',
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField('tipo', max_length=20, choices=KINDS)
    text = models.CharField('texto', max_length=300)
    read_at = models.DateTimeField('lida em', null=True, blank=True)

    class Meta:
        ordering = ('-created', '-id')
        indexes = [models.Index(fields=['user', 'read_at'])]
        verbose_name = 'notificação'
        verbose_name_plural = 'notificações'

    def __str__(self):
        return f'{self.get_kind_display()} para {self.user}'


class CustomField(UuidModel, TimeStampedModel):
    """Campo extra dos cards de um projeto (ex.: Prioridade, Cliente final)."""

    KINDS = {'text': 'Texto', 'number': 'Número', 'date': 'Data', 'select': 'Seleção', 'bool': 'Sim/não'}

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='custom_fields')
    name = models.CharField('nome', max_length=80)
    kind = models.CharField('tipo', max_length=10, choices=KINDS)
    options = models.JSONField('opções', default=list, blank=True)  # só para seleção
    required = models.BooleanField('obrigatório', default=False)
    position = models.PositiveIntegerField('ordem', default=0)

    class Meta:
        ordering = ('position', 'id')
        constraints = [models.UniqueConstraint(Lower('name'), 'project', name='unique_custom_field_name_per_project')]
        verbose_name = 'campo personalizado'
        verbose_name_plural = 'campos personalizados'

    def __str__(self):
        return self.name

    def clean(self):
        if self.kind == 'select':
            if not self.options:
                raise ValidationError({'options': 'Informe ao menos uma opção.'})
            if len({o.strip().lower() for o in self.options}) != len(self.options):
                raise ValidationError({'options': 'Há opção repetida.'})
        elif self.options:
            raise ValidationError({'options': 'Opções só valem para o tipo seleção.'})

    def clean_value(self, value):
        """Valor válido para o tipo do campo (já normalizado) ou ValidationError com o nome do campo."""
        from datetime import date

        def invalid(what):
            return ValidationError(f'{self.name}: {what}.')

        if self.kind == 'text':
            return str(value).strip()
        if self.kind == 'number':
            if isinstance(value, bool):
                raise invalid('informe um número')
            try:
                return value if isinstance(value, int | float) else float(str(value).replace(',', '.'))
            except ValueError:
                raise invalid('informe um número')
        if self.kind == 'date':
            try:
                return date.fromisoformat(str(value)).isoformat()
            except ValueError:
                raise invalid('informe a data como AAAA-MM-DD')
        if self.kind == 'select':
            if value not in self.options:
                raise invalid(f'escolha uma opção ({", ".join(self.options)})')
            return value
        if not isinstance(value, bool):
            raise invalid('informe sim/não (true ou false)')
        return value

    def save(self, *args, **kwargs):
        if self._state.adding and not self.position:
            last = CustomField.objects.filter(project_id=self.project_id).aggregate(last=Max('position'))['last']
            self.position = 0 if last is None else last + 1
        super().save(*args, **kwargs)
