from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum

from hubflow.core.models import TimeStampedModel
from hubflow.sprints.models import Sprint
from hubflow.timetracking.models import TimeEntry

CENTS = Decimal('0.01')


class Payment(TimeStampedModel):
    """Faturamento por sprint (RN-80, RN-81)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID = 'paid', 'Pago'

    sprint = models.ForeignKey(Sprint, on_delete=models.PROTECT, related_name='payments', verbose_name='sprint')
    description = models.CharField('descrição', max_length=200, blank=True)
    hourly_rate = models.DecimalField(
        'valor por hora', max_digits=10, decimal_places=2, validators=[MinValueValidator(CENTS)]
    )
    estimated_hours = models.DecimalField('horas estimadas', max_digits=8, decimal_places=2, null=True, blank=True)
    fixed_value = models.DecimalField(
        'valor fechado',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Se informado, vale no lugar de horas × valor/hora.',
    )
    invoice_number = models.CharField('número da NF', max_length=50, blank=True)
    issue_date = models.DateField('emissão', null=True, blank=True)
    payment_date = models.DateField('pagamento', null=True, blank=True)
    status = models.CharField('situação', max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ('-issue_date', '-id')
        verbose_name = 'pagamento'
        verbose_name_plural = 'pagamentos'

    def __str__(self):
        return f'{self.project} · {self.sprint} · {self.get_status_display()}'

    @property
    def project(self):
        return self.sprint.project

    @property
    def client(self):
        return self.sprint.project.client

    @property
    def estimated_value(self):
        if self.estimated_hours is None:
            return None
        return (self.estimated_hours * self.hourly_rate).quantize(CENTS, ROUND_HALF_UP)

    @property
    def spent_hours(self):
        # RN-80: soma das entradas fechadas dos cards da sprint.
        total = TimeEntry.objects.filter(card__sprint=self.sprint, ended_at__isnull=False).aggregate(
            total=Sum(F('ended_at') - F('started_at'))
        )['total']
        hours = Decimal(total.total_seconds()) / Decimal(3600) if total else Decimal(0)
        return hours.quantize(CENTS, ROUND_HALF_UP)

    @property
    def total_value(self):
        if self.fixed_value is not None:
            return self.fixed_value
        return (self.spent_hours * self.hourly_rate).quantize(CENTS, ROUND_HALF_UP)

    def pay(self):
        # RN-81
        self.status = self.Status.PAID
        self.payment_date = date.today()
        self.save(update_fields=['status', 'payment_date', 'modified'])

    def copy(self):
        # RN-81: duplica como pendente, sem NF nem datas.
        return Payment.objects.create(
            sprint=self.sprint,
            description=self.description,
            hourly_rate=self.hourly_rate,
            estimated_hours=self.estimated_hours,
            fixed_value=self.fixed_value,
        )
