from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum

from hubflow.core.models import TimeStampedModel
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint
from hubflow.timetracking.models import TimeEntry

CENTS = Decimal('0.01')


class Payment(TimeStampedModel):
    """Faturamento por sprint (RN-80, RN-81)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID = 'paid', 'Pago'

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='payments', verbose_name='projeto')
    # Sprint opcional: sem ela, o pagamento cobre um período (ex.: o mês).
    sprint = models.ForeignKey(
        Sprint, null=True, blank=True, on_delete=models.PROTECT, related_name='payments', verbose_name='sprint'
    )
    period_start = models.DateField('início do período', null=True, blank=True)
    period_end = models.DateField('fim do período', null=True, blank=True)
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
        return f'{self.project} · {self.scope} · {self.get_status_display()}'

    @property
    def scope(self):
        if self.sprint_id:
            return str(self.sprint)
        return f'{self.period_start:%d/%m/%Y} a {self.period_end:%d/%m/%Y}'

    @property
    def client(self):
        return self.project.client

    def clean(self):
        if self.sprint_id is None and not (self.period_start and self.period_end):
            raise ValidationError('Informe a sprint ou o período (início e fim).')
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError({'period_end': 'O fim do período não pode ser antes do início.'})
        if self.sprint_id and self.project_id and self.sprint.project_id != self.project_id:
            raise ValidationError({'sprint': 'A sprint precisa ser deste projeto.'})

    def save(self, *args, **kwargs):
        if self.sprint_id and not self.project_id:
            self.project = self.sprint.project
        super().save(*args, **kwargs)

    @property
    def estimated_value(self):
        if self.estimated_hours is None:
            return None
        return (self.estimated_hours * self.hourly_rate).quantize(CENTS, ROUND_HALF_UP)

    def time_entries(self):
        """RN-80: entradas fechadas da sprint ou, sem sprint, do projeto dentro do período."""
        entries = TimeEntry.objects.filter(ended_at__isnull=False)
        if self.sprint_id:
            return entries.filter(card__sprint_id=self.sprint_id)
        return entries.filter(
            card__project_id=self.project_id,
            started_at__date__gte=self.period_start,
            started_at__date__lte=self.period_end,
        )

    @property
    def spent_hours(self):
        total = self.time_entries().aggregate(total=Sum(F('ended_at') - F('started_at')))['total']
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
        # RN-81: duplica como pendente, sem NF nem datas; pagamento por período avança para o mês seguinte.
        period_start = period_end = None
        if self.period_start and self.period_end:
            period_start, period_end = next_month(self.period_start)
        return Payment.objects.create(
            project=self.project,
            sprint=self.sprint,
            period_start=period_start,
            period_end=period_end,
            description=self.description,
            hourly_rate=self.hourly_rate,
            estimated_hours=self.estimated_hours,
            fixed_value=self.fixed_value,
        )


def month_bounds(year, month):
    """Primeiro e último dia do mês."""
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return start, end


def next_month(day):
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    return month_bounds(year, month)
