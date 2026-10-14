from ninja import Schema


class RepoSettingsIn(Schema):
    token: str | None = None  # None = mantém o atual; '' = apaga
    gitlab_project_id: int | None = None
    create_issues: bool = False
    webhook_secret: str | None = None  # None = mantém; '' = apaga


class RepoSettingsOut(Schema):
    has_token: bool
    gitlab_project_id: int | None
    create_issues: bool
    provider: str
    repository_url: str
    has_webhook_secret: bool
    webhook_path: str

    @staticmethod
    def resolve_has_token(project):
        return bool(project.repo_token)

    @staticmethod
    def resolve_has_webhook_secret(project):
        return bool(project.webhook_secret)

    @staticmethod
    def resolve_webhook_path(project):
        return f'/api/webhooks/{project.provider}/{project.id}'


class RepoCheckOut(Schema):
    ok: bool
    name: str
    private: bool
    open_issues: int


class ImportIssuesIn(Schema):
    include_closed: bool = False


class ImportIssuesOut(Schema):
    created: int
    skipped: int
