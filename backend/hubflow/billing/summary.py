"""Resumo financeiro agregado no banco (recebido/pendente, por cliente, por mês)."""

from decimal import Decimal

from django.db.models import Case, DecimalField, ExpressionWrapper, F, FloatField, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, Extract, Round, TruncMonth

from hubflow.timetracking.models import TimeEntry

from .models import Payment

MONEY = DecimalField(max_digits=14, decimal_places=2)
ZERO = Decimal('0.00')


def valued_payments():
    """Pagamentos com `value` calculado em SQL: valor fechado ou horas da sprint × valor/hora (RN-80)."""
    sprint_seconds = (
        TimeEntry.objects.filter(card__sprint_id=OuterRef('sprint_id'), ended_at__isnull=False)
        .values('card__sprint_id')
        .annotate(seconds=Extract(Sum(F('ended_at') - F('started_at')), 'epoch'))
        .values('seconds')[:1]
    )
    # Horas arredondadas a 2 casas antes de multiplicar, igual a Payment.spent_hours.
    seconds = Coalesce(Subquery(sprint_seconds, output_field=FloatField()), Value(0.0), output_field=FloatField())
    hours = Round(ExpressionWrapper(seconds / Value(3600.0), output_field=FloatField()), 2, output_field=FloatField())
    hours_value = ExpressionWrapper(F('hourly_rate') * hours, output_field=MONEY)
    return Payment.objects.annotate(value=Coalesce(F('fixed_value'), hours_value, output_field=MONEY))


def _split(queryset):
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
        payments = payments.filter(sprint__project__client_id=client_id)
    scoped = payments.filter(issue_date__year=year) if year else payments

    totals = scoped.aggregate(**_split(scoped))
    by_client = (
        scoped.values(client_id=F('sprint__project__client_id'), client_name=F('sprint__project__client__name'))
        .annotate(**_split(scoped))
        .order_by('-received', 'client_name')
    )
    by_month = (
        scoped.filter(issue_date__isnull=False)
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(**_split(scoped))
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
