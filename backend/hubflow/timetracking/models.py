from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from hubflow.boards.models import Card
from hubflow.core.models import CreatedModel

from .managers import TimeEntryManager


class TimeEntry(CreatedModel):
    """Tempo gasto num card: cronômetro (aberto até ended_at) ou lançamento manual."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_entries')
    started_at = models.DateTimeField('início')
    ended_at = models.DateTimeField('fim', null=True, blank=True)
    note = models.CharField('nota', max_length=200, blank=True)
    is_manual = models.BooleanField('lançamento manual', default=False)

    objects = TimeEntryManager()

    class Meta:
        ordering = ('-started_at', '-id')
        verbose_name = 'entrada de tempo'
        verbose_name_plural = 'entradas de tempo'

    def __str__(self):
        return f'{self.card} · {self.user} · {self.hours:.2f}h'

    @property
    def is_running(self):
        return self.ended_at is None

    @property
    def duration(self):
        return (self.ended_at - self.started_at) if self.ended_at else None

    @property
    def hours(self):
        return self.duration.total_seconds() / 3600 if self.duration else 0.0

    def clean(self):
        if self.ended_at and self.ended_at < self.started_at:
            raise ValidationError({'ended_at': 'O fim não pode ser antes do início.'})
        # RN-70: um cronômetro aberto por card.
        if self.ended_at is None:
            running = TimeEntry.objects.filter(card_id=self.card_id, ended_at__isnull=True).exclude(id=self.id)
            if running.exists():
                raise ValidationError('Este card já tem um cronômetro aberto.')
