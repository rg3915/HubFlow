from django.test import Client


def test_health_responde_ok():
    response = Client().get('/api/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
