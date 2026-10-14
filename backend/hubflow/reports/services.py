"""Relatório de um cliente ou projeto num período: horas, cards, SLA e faturamento (RN-120)."""

import calendar
from datetime import timedelta

from django.db.models import Avg, Count, F, Min, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja.errors import HttpError

from hubflow.billing.summary import money, split_totals, valued_payments
from hubflow.boards.models import Card, CardEvent, CardMove, Column
from hubflow.permissions.services import has_perm, visible_clients, visible_payments, visible_projects
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


def resolve_period(period, ref, start, end):
    """Período pronto (week/fortnight/month + data) ou datas livres (start/end)."""
    if period:
        if period not in PERIODS or ref is None:
            raise HttpError(400, f'Use period ({", ".join(PERIODS)}) com date=AAAA-MM-DD, ou start e end.')
        start, end = period_bounds(period, ref)
        return {'kind': period, 'label': PERIODS[period], 'start': start, 'end': end}
    if not (start and end) or start > end:
        raise HttpError(400, 'Informe start e end (AAAA-MM-DD), com start antes de end, ou period e date.')
    return {'kind': 'custom', 'label': 'Período', 'start': start, 'end': end}


def report_for(user, client=None, project=None, period=None, ref=None, start=None, end=None):
    """Relatório já limitado ao que a pessoa enxerga (clientes, projetos e pagamentos)."""
    window = resolve_period(period, ref, start, end)
    scope = {'client': None, 'project': None}
    if client:
        scope['client'] = get_object_or_404(visible_clients(user), id=client).name
    if project:
        scope['project'] = get_object_or_404(visible_projects(user), id=project).name
    sees_payments = has_perm(user, 'billing.view_payment') or has_perm(user, 'permissions.view_own_payments')
    report = build_report(
        window['start'],
        window['end'],
        client_id=client,
        project_id=project,
        projects=visible_projects(user),
        with_billing=sees_payments,
        payments=visible_payments(user),
    )
    return report | {'period': window, 'scope': scope}


def default_recipients(user, client, project):
    if project:
        return get_object_or_404(visible_projects(user), id=project).notification_emails
    if client:
        return get_object_or_404(visible_clients(user), id=client).emails
    return []


def last_finished_period(frequency, today):
    """O período mais recente já encerrado (o anterior ao que contém `today`)."""
    current_start, _ = period_bounds(frequency, today)
    return period_bounds(frequency, current_start - timedelta(days=1))


def send_due_reports(today=None):
    """Envia, uma vez, o relatório de cada período encerrado dos agendamentos ligados. Devolve quantos saíram."""
    from .mail import send_report_email
    from .models import ReportSchedule

    today = today or timezone.localdate()
    sent = 0
    schedules = ReportSchedule.objects.filter(is_active=True, created_by__is_active=True).select_related('created_by')
    for schedule in schedules:
        start, end = last_finished_period(schedule.frequency, today)
        if schedule.last_period_end and schedule.last_period_end >= end:
            continue
        user = schedule.created_by
        recipients = schedule.emails or default_recipients(user, schedule.client_id, schedule.project_id)
        if not recipients:
            continue
        report = report_for(user, schedule.client_id, schedule.project_id, schedule.frequency, start)
        send_report_email(report, recipients)
        schedule.last_period_end = end
        schedule.save(update_fields=['last_period_end', 'modified'])
        sent += 1
    return sent
