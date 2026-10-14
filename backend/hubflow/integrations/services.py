from hubflow.boards.activity import record
from hubflow.boards.models import Card, Column
from hubflow.boards.services import resolve_sprint

from .client import RepoClient


def import_issues(project, user=None, include_closed=False):
    """Traz as issues do repositório como cards (sem duplicar; PRs ficam de fora; fechadas vão para Concluído)."""
    existing = set(project.cards.exclude(issue_number=None).values_list('issue_number', flat=True))
    sprint = resolve_sprint(project)
    created = skipped = 0
    for issue in RepoClient(project).list_issues(include_closed):
        if issue['is_pull'] or issue['number'] in existing:
            skipped += 1
            continue
        card = Card.objects.create(
            project=project,
            sprint=sprint,
            title=issue['title'],
            description=issue['body'],
            column=Column.DONE if issue['closed'] else Column.BACKLOG,
            issue_number=issue['number'],
            issue_url=issue['url'],
            created_by=user,
        )
        record(card, 'created', user, imported=True)
        created += 1
    return {'created': created, 'skipped': skipped}
