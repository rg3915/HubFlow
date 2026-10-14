"""Relatório de um cliente ou projeto num período: horas, cards, SLA e faturamento (RN-120)."""

import calendar
from datetime import timedelta

from django.db.models import Avg, Count, F, Min, Sum

from hubflow.billing.summary import money, split_totals, valued_payments
from hubflow.boards.models import Card, CardEvent, CardMove, Column
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry

PERIODS = {'week': 'Semana', 'fortnight': 'Quinzena', 'month': 'Mês'}


def period_bounds(kind, ref):
    """(início, fim) do período que contém `ref`: semana seg–dom, quinzena 1–15/16–fim, mês."""
    last_day = calendar.monthrange(ref.year, ref.month)[1]
    if kind == 'week':
        start = ref - timedelta(days=ref.weekday())
        return start, start + timedelta(days=6)
    if kind == 'fortnight':
        first_half = ref.day <= 15
        return ref.replace(day=1 if first_half else 16), ref.replace(day=15 if first_half else last_day)
    if kind == 'month':
        return ref.replace(day=1), ref.replace(day=last_day)
    raise ValueError(f'Período desconhecido: {kind}')


def hours(duration):
    return round(duration.total_seconds() / 3600, 2) if duration else 0.0


def scoped_projects(projects=None, client_id=None, project_id=None):
    projects = Project.objects.all() if projects is None else projects
    if client_id:
        projects = projects.filter(client_id=client_id)
    if project_id:
        projects = projects.filter(id=project_id)
    return projects


def hours_section(projects, start, end):
    entries = TimeEntry.objects.filter(
        card__project__in=projects, ended_at__isnull=False, started_at__date__gte=start, started_at__date__lte=end
    )
    spent = Sum(F('ended_at') - F('started_at'))
    by_user = entries.values('user__name', 'user__email').annotate(total=spent).order_by('-total', 'user__email')
    by_card = (
        entries.values('card__project__name', 'card__number', 'card__title')
        .annotate(total=spent)
        .order_by('-total', 'card__project__name', 'card__number')[:10]
    )
    return {
        'total': hours(entries.aggregate(total=spent)['total']),
        'by_user': [{'name': r['user__name'] or r['user__email'], 'hours': hours(r['total'])} for r in by_user],
        'by_card': [
            {
                'project': r['card__project__name'],
                'number': r['card__number'],
                'title': r['card__title'],
                'hours': hours(r['total']),
            }
            for r in by_card
        ],
    }


def cards_section(projects, start, end):
    in_period = {'created__date__gte': start, 'created__date__lte': end}
    created = Card.objects.filter(project__in=projects, **in_period).count()
    done = (
        CardMove.objects.filter(card__project__in=projects, to_column=Column.DONE, **in_period)
        .values('card')
        .annotate(done_at=Min('created'), card_created=Min('card__created'))
        .aggregate(total=Count('card'), lead=Avg(F('done_at') - F('card_created')))
    )
    lead = round(done['lead'].total_seconds() / 86400, 1) if done['lead'] else None
    return {'created': created, 'done': done['total'], 'avg_days_to_done': lead}


def billing_section(projects, start, end, payments=None):
    payments = valued_payments(payments).filter(project__in=projects, issue_date__gte=start, issue_date__lte=end)
    totals = payments.aggregate(**split_totals(payments))
    return {'received': money(totals['received']), 'pending': money(totals['pending'])}


def build_report(start, end, client_id=None, project_id=None, with_billing=True, projects=None, payments=None):
    """`projects`/`payments` limitam ao que a pessoa enxerga (a API passa os visíveis)."""
    projects = scoped_projects(projects, client_id, project_id)
    sla = CardEvent.objects.filter(
        card__project__in=projects, kind='sla_breached', created__date__gte=start, created__date__lte=end
    ).count()
    return {
        'period': {'start': start, 'end': end},
        'hours': hours_section(projects, start, end),
        'cards': cards_section(projects, start, end),
        'sla_breached': sla,
        'billing': billing_section(projects, start, end, payments) if with_billing else None,
    }
