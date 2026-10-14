from ninja import Schema


class RepoSettingsIn(Schema):
    token: str | None = None  # None = mantém o atual; '' = apaga
    gitlab_project_id: int | None = None
    create_issues: bool = False


class RepoSettingsOut(Schema):
    has_token: bool
    gitlab_project_id: int | None
    create_issues: bool
    provider: str
    repository_url: str

    @staticmethod
    def resolve_has_token(project):
        return bool(project.repo_token)


class RepoCheckOut(Schema):
    ok: bool
    name: str
    private: bool
    open_issues: int
