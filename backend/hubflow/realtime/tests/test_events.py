import json

import pytest
from django.conf import settings

from hubflow.realtime.events import channel_for, publish, subscribe


def test_settings_tem_redis_url():
    assert settings.REDIS_URL.startswith('redis://')


def test_canal_do_projeto():
    assert channel_for(7) == 'hubflow:project:7'


@pytest.mark.django_db
def test_publica_e_recebe_evento_no_canal_do_projeto():
    with subscribe(7) as messages:
        publish(7, 'card_moved', {'card_id': 1, 'to_column': 'qa'})

        event = next(messages)

    assert event == {'type': 'card_moved', 'project_id': 7, 'data': {'card_id': 1, 'to_column': 'qa'}}


@pytest.mark.django_db
def test_eventos_de_outro_projeto_nao_chegam():
    with subscribe(8) as messages:
        publish(9, 'card_created', {})
        publish(8, 'card_created', {'card_id': 2})

        event = next(messages)

    assert event['project_id'] == 8


def test_evento_e_json_serializavel():
    assert json.loads(json.dumps({'type': 'x', 'project_id': 1, 'data': {}}))
