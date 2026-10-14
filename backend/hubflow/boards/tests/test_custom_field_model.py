import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from hubflow.boards.models import CustomField

pytestmark = pytest.mark.django_db


def test_cria_campo_com_ordem_no_fim(loja):
    first = CustomField.objects.create(project=loja, name='Cliente final', kind='text')
    second = CustomField.objects.create(project=loja, name='Prioridade', kind='select', options=['Alta', 'Baixa'])

    assert (first.position, second.position) == (0, 1)
    assert list(loja.custom_fields.values_list('name', flat=True)) == ['Cliente final', 'Prioridade']
    assert first.uuid.version == 7 and first.required is False


def test_nome_unico_no_projeto_sem_diferenciar_maiusculas(loja):
    CustomField.objects.create(project=loja, name='Prioridade', kind='text')

    with pytest.raises(IntegrityError):
        CustomField.objects.create(project=loja, name='prioridade', kind='text')


@pytest.mark.parametrize(
    ('kind', 'options', 'message'),
    [
        ('select', [], 'opção'),
        ('select', ['Alta', 'alta'], 'repetida'),
        ('text', ['Alta'], 'seleção'),
        ('cor', [], 'válida'),
    ],
)
def test_validacao(loja, kind, options, message):
    with pytest.raises(ValidationError, match=message):
        CustomField(project=loja, name='Campo', kind=kind, options=options).full_clean()
