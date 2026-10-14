"""Webhooks do GitHub e do GitLab: commit ou PR/MR mesclado com 'close #N' conclui o card."""

import hashlib
import hmac
import re

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from hubflow.boards.models import Column
from hubflow.boards.services import move_card
from hubflow.projects.models import Project

CLOSE_KEYWORDS = re.compile(r'\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)', re.IGNORECASE)


def issue_numbers(*texts):
    return {int(n) for text in texts if text for n in CLOSE_KEYWORDS.findall(text)}


def close_cards(project, numbers):
    """Move para Concluído os cards do projeto ligados às issues; a issue já foi fechada pelo próprio commit."""
    moved = []
    cards = project.cards.filter(issue_number__in=numbers).exclude(column__in=(Column.DONE, Column.ARCHIVED))
    for card in cards.order_by('issue_number'):
        move_card(card, Column.DONE, sync=False)
        moved.append(card.issue_number)
    return moved


def github_signature_ok(request, secret):
    expected = 'sha256=' + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, request.headers.get('X-Hub-Signature-256', ''))


def github_texts(event, payload):
    if event == 'push':
        return [commit.get('message', '') for commit in payload.get('commits', [])]
    if event == 'pull_request' and payload.get('action') == 'closed' and payload.get('pull_request', {}).get('merged'):
        pull = payload['pull_request']
        return [pull.get('title', ''), pull.get('body') or '']
    return []


def gitlab_texts(payload):
    kind = payload.get('object_kind')
    if kind == 'push':
        return [commit.get('message', '') for commit in payload.get('commits', [])]
    if kind == 'merge_request' and payload.get('object_attributes', {}).get('state') == 'merged':
        attrs = payload['object_attributes']
        return [attrs.get('title', ''), attrs.get('description') or '']
    return []


@csrf_exempt
@require_POST
def github_webhook(request, project_id):
    import json

    project = get_object_or_404(Project, id=project_id)
    if not project.webhook_secret or not github_signature_ok(request, project.webhook_secret):
        return HttpResponseForbidden('Assinatura inválida.')
    payload = json.loads(request.body or b'{}')
    texts = github_texts(request.headers.get('X-GitHub-Event', ''), payload)
    return JsonResponse({'moved': close_cards(project, issue_numbers(*texts))})


@csrf_exempt
@require_POST
def gitlab_webhook(request, project_id):
    import json

    project = get_object_or_404(Project, id=project_id)
    token = request.headers.get('X-Gitlab-Token', '')
    if not project.webhook_secret or not hmac.compare_digest(token, project.webhook_secret):
        return HttpResponseForbidden('Token inválido.')
    payload = json.loads(request.body or b'{}')
    return JsonResponse({'moved': close_cards(project, issue_numbers(*gitlab_texts(payload)))})
