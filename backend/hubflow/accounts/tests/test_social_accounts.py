import pytest

from hubflow.accounts.models import SocialAccount

pytestmark = pytest.mark.django_db


def test_lista_e_desvincula_as_contas(api, user, django_user_model):
    SocialAccount.objects.create(user=user, provider='github', uid='42', email='ana@example.com')
    other = django_user_model.objects.create_user(email='bob@hubflow.com', password='x')
    SocialAccount.objects.create(user=other, provider='google', uid='9')

    data = api.get('/api/auth/social').json()

    assert [(a['provider'], a['name'], a['email']) for a in data] == [('github', 'GitHub', 'ana@example.com')]
    assert api.delete('/api/auth/social/github').status_code == 204
    assert not SocialAccount.objects.filter(user=user).exists()
    assert api.delete('/api/auth/social/google').status_code == 404  # a do Bob não é sua
