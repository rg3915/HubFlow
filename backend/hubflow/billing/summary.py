"""Resumo financeiro agregado no banco (recebido/pendente, por cliente, por mês)."""

from decimal import Decimal

from django.db.models import Case, DecimalField, ExpressionWrapper, F, FloatField, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Extract, Round, TruncMonth

from hubflow.timetracking.models import TimeEntry

from .models import Payment

MONEY = DecimalField(max_digits=14, decimal_places=2)
ZERO = Decimal('0.00')


def _seconds(entries, group_by):
    return (
        entries.values(group_by)
        .annotate(seconds=Extract(Sum(F('ended_at') - F('started_at')), 'epoch'))
        .values('seconds')[:1]
    )


def valued_payments():
    """Pagamentos com `value` em SQL: valor fechado ou horas × valor/hora (RN-80).

    Horas = entradas da sprint ou, sem sprint, do projeto dentro do período.
    """
    closed = TimeEntry.objects.filter(ended_at__isnull=False)
    sprint_seconds = _seconds(closed.filter(card__sprint_id=OuterRef('sprint_id')), 'card__sprint_id')
    period_seconds = _seconds(
        closed.filter(
            card__project_id=OuterRef('project_id'),
            started_at__date__gte=OuterRef('period_start'),
            started_at__date__lte=OuterRef('period_end'),
        ),
        'card__project_id',
    )
    scoped_seconds = Case(
        When(sprint__isnull=False, then=Subquery(sprint_seconds, output_field=FloatField())),
        default=Subquery(period_seconds, output_field=FloatField()),
        output_field=FloatField(),
    )
    # Horas arredondadas a 2 casas antes de multiplicar, igual a Payment.spent_hours.
    seconds = Coalesce(scoped_seconds, Value(0.0), output_field=FloatField())
    hours = Round(ExpressionWrapper(seconds / Value(3600.0), output_field=FloatField()), 2, output_field=FloatField())
    hours_value = ExpressionWrapper(F('hourly_rate') * hours, output_field=MONEY)
    return Payment.objects.annotate(value=Coalesce(F('fixed_value'), hours_value, output_field=MONEY))


def split_totals(queryset):
    """Soma de `value` separada em recebido (pago) e pendente."""
    return {
        'received': Coalesce(
            Sum(Case(When(status='paid', then=F('value')), output_field=MONEY)), Value(ZERO), output_field=MONEY
        ),
        'pending': Coalesce(
            Sum(Case(When(status='pending', then=F('value')), output_field=MONEY)), Value(ZERO), output_field=MONEY
        ),
    }


def money(value):
    return (value or ZERO).quantize(ZERO)


def payments_summary(client_id=None, year=None):
    payments = valued_payments()
    if client_id:
        payments = payments.filter(project__client_id=client_id)
    scoped = payments.filter(issue_date__year=year) if year else payments

    totals = scoped.aggregate(**split_totals(scoped))
    by_client = (
        scoped.values(client_id=F('project__client_id'), client_name=F('project__client__name'))
        .annotate(**split_totals(scoped))
        .order_by('-received', 'client_name')
    )
    by_month = (
        scoped.filter(issue_date__isnull=False)
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(**split_totals(scoped))
        .order_by('month')
    )
    years = payments.filter(issue_date__isnull=False).dates('issue_date', 'year', order='DESC')
    return {
        'received': money(totals['received']),
        'pending': money(totals['pending']),
        'by_client': [
            {**row, 'received': money(row['received']), 'pending': money(row['pending'])} for row in by_client
        ],
        'by_month': [
            {
                'month': row['month'].strftime('%Y-%m'),
                'received': money(row['received']),
                'pending': money(row['pending']),
            }
            for row in by_month
        ],
        'years': [d.year for d in years],
    }
