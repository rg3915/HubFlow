from datetime import datetime, time, timedelta

from django.db import models
from django.db.models import F, Sum
from django.utils import timezone


class TimeEntryManager(models.Manager):
    def running_for(self, card):
        return self.filter(card=card, ended_at__isnull=True).first()

    def total_for(self, card):
        """Soma das entradas fechadas do card (as abertas ainda não contam)."""
        closed = self.filter(card=card, ended_at__isnull=False)
        total = closed.aggregate(total=Sum(F('ended_at') - F('started_at')))['total']
        return total or timedelta()

    def manual(self, card, user, hours, date, note=''):
        """RN-72: lançamento manual de horas numa data (começa às 09:00 daquele dia)."""
        start = timezone.make_aware(datetime.combine(date, time(9, 0)))
        return self.create(
            card=card,
            user=user,
            started_at=start,
            ended_at=start + timedelta(hours=hours),
            note=note,
            is_manual=True,
        )
