"""Cliente mínimo para GitHub e GitLab (REST), um por projeto."""

import httpx

GITHUB_API = 'https://api.github.com'
GITLAB_API = 'https://gitlab.com/api/v4'
TIMEOUT = 10


class RepoError(Exception):
    pass


class RepoClient:
    def __init__(self, project):
        if not project.repo_token:
            raise RepoError('O projeto não tem token do repositório. Configure em Integração.')
        self.project = project
        self.is_github = project.provider == 'github'
        if self.is_github:
            self.base = f'{GITHUB_API}/repos/{project.owner}/{project.repo}'
            headers = {'Authorization': f'Bearer {project.repo_token}', 'Accept': 'application/vnd.github+json'}
        else:
            if not project.gitlab_project_id:
                raise RepoError('Informe o id numérico do projeto no GitLab.')
            self.base = f'{GITLAB_API}/projects/{project.gitlab_project_id}'
            headers = {'PRIVATE-TOKEN': project.repo_token}
        self.http = httpx.Client(headers=headers, timeout=TIMEOUT)

    def request(self, method, path='', **kwargs):
        try:
            response = self.http.request(method, f'{self.base}{path}', **kwargs)
        except httpx.HTTPError as error:
            raise RepoError(f'Não foi possível falar com o repositório: {error}')
        if response.status_code == 401:
            raise RepoError('O repositório recusou as credenciais (401). Confira o token.')
        if response.status_code == 404:
            raise RepoError('Repositório não encontrado (404). Confira owner/repo e as permissões do token.')
        if response.status_code >= 400:
            raise RepoError(f'O repositório respondeu {response.status_code}: {response.text[:200]}')
        return response.json()

    def check(self):
        data = self.request('GET')
        if self.is_github:
            return {
                'ok': True,
                'name': data['full_name'],
                'private': data['private'],
                'open_issues': data['open_issues_count'],
            }
        return {
            'ok': True,
            'name': data['path_with_namespace'],
            'private': data.get('visibility') == 'private',
            'open_issues': data.get('open_issues_count', 0),
        }

    def create_issue(self, title, body=''):
        """Cria a issue no repositório; devolve (número, url)."""
        if self.is_github:
            data = self.request('POST', '/issues', json={'title': title, 'body': body})
            return data['number'], data['html_url']
        data = self.request('POST', '/issues', json={'title': title, 'description': body})
        return data['iid'], data['web_url']

    def update_issue(self, number, title, body=''):
        if self.is_github:
            return self.request('PATCH', f'/issues/{number}', json={'title': title, 'body': body})
        return self.request('PUT', f'/issues/{number}', json={'title': title, 'description': body})

    def set_issue_state(self, number, closed):
        if self.is_github:
            return self.request('PATCH', f'/issues/{number}', json={'state': 'closed' if closed else 'open'})
        return self.request('PUT', f'/issues/{number}', json={'state_event': 'close' if closed else 'reopen'})

    def list_issues(self, include_closed=False):
        """Issues do repositório normalizadas: número, título, corpo, url, fechada, é_pull."""
        if self.is_github:
            state = 'all' if include_closed else 'open'
            issues = self.request('GET', '/issues', params={'state': state, 'per_page': 100})
            return [
                {
                    'number': issue['number'],
                    'title': issue['title'],
                    'body': issue.get('body') or '',
                    'url': issue['html_url'],
                    'closed': issue['state'] == 'closed',
                    'is_pull': 'pull_request' in issue,
                }
                for issue in issues
            ]
        state = 'all' if include_closed else 'opened'
        issues = self.request('GET', '/issues', params={'state': state, 'per_page': 100})
        return [
            {
                'number': issue['iid'],
                'title': issue['title'],
                'body': issue.get('description') or '',
                'url': issue['web_url'],
                'closed': issue['state'] == 'closed',
                'is_pull': False,
            }
            for issue in issues
        ]
