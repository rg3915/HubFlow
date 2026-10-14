import json

import pytest
import respx
from httpx import Response

from hubflow_cli.config import save_config
from tests.test_card import PROJECTS


@pytest.fixture(autouse=True)
def logged_in():
    save_config({'url': 'http://api.test', 'token': 'abc123'})


@respx.mock
def test_project_create_full_cria_tudo_de_uma_vez(run):
    created = {
        'client': {'id': 1, 'name': 'ACME', 'emails': [], 'is_active': True},
        'project': PROJECTS[0],
        'sprint': {'id': 3, 'number': 1, 'name': ''},
        'milestone': {'id': 2, 'title': 'v1.0'},
    }
    route = respx.post('http://api.test/api/projects/full').mock(return_value=Response(201, json=created))

    result = run(
        'project',
        'create',
        'Loja',
        '--client',
        'ACME',
        '--provider',
        'github',
        '--repo',
        'acme/loja',
        '--full',
        '--milestone',
        'v1.0',
    )

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.read())
    assert body['client_name'] == 'ACME' and body['milestone_title'] == 'v1.0' and body['repo'] == 'loja'
    assert 'Sprint 1' in result.output and 'v1.0' in result.output and 'ACME' in result.output
