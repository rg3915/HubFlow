from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from hubflow.permissions.services import has_perm, visible_clients, visible_payments, visible_projects

from .pdf import file_name, render_report_pdf
from .schemas import ReportOut
from .services import PERIODS, build_report, period_bounds

router = Router(tags=['reports'])


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


@router.get('', response=ReportOut)
def get_report(
    request,
    client: int | None = None,
    project: int | None = None,
    period: str | None = None,
    date: date | None = None,
    start: date | None = None,
    end: date | None = None,
):
    return report_for(request.user, client, project, period, date, start, end)


@router.get('/pdf')
def get_report_pdf(
    request,
    client: int | None = None,
    project: int | None = None,
    period: str | None = None,
    date: date | None = None,
    start: date | None = None,
    end: date | None = None,
):
    report = report_for(request.user, client, project, period, date, start, end)
    response = HttpResponse(render_report_pdf(report), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name(report)}"'
    return response
