import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from hubflow.clients.models import Client

pytestmark = pytest.mark.django_db


def test_cria_cliente_com_nome():
    client = Client.objects.create(name='ACME')

    assert client.name == 'ACME'
    assert client.is_active is True
    assert client.emails == []
    assert str(client) == 'ACME'


def test_nome_e_unico():
    # RN-10
    Client.objects.create(name='ACME')

    with pytest.raises(IntegrityError):
        Client.objects.create(name='ACME')


def test_nome_e_obrigatorio():
    with pytest.raises(ValidationError):
        Client(name='').full_clean()


def test_aceita_lista_de_emails():
    # RN-12
    client = Client.objects.create(name='ACME', emails=['ana@acme.com', 'bob@acme.com'])
    client.full_clean()

    client.refresh_from_db()
    assert client.emails == ['ana@acme.com', 'bob@acme.com']


def test_rejeita_email_invalido_na_lista():
    with pytest.raises(ValidationError):
        Client(name='ACME', emails=['nao-e-email']).full_clean()


def test_ordena_por_nome():
    Client.objects.create(name='Zeta')
    Client.objects.create(name='Alfa')

    assert list(Client.objects.values_list('name', flat=True)) == ['Alfa', 'Zeta']
