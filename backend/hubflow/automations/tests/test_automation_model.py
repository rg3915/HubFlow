import pytest
from django.core.exceptions import ValidationError

from hubflow.automations.models import Automation
from hubflow.boards.models import Label

pytestmark = pytest.mark.django_db


def build(loja, **data):
    return Automation(project=loja, name='Regra', **data)


def test_descricao_em_linguagem_simples(loja, user):
    bug = Label.objects.create(project=loja, name='bug')
    rules = [
        build(loja, trigger='entered_column', trigger_column='qa', action='move', action_column='done'),
        build(loja, trigger='created', action='assign', action_user=user),
        build(loja, trigger='created', action='add_label', action_label=bug),
        build(loja, trigger='sla_breached', action='notify'),
    ]

    assert [rule.describe() for rule in rules] == [
        'Quando o card entrar em QA → mover para Concluído',
        'Quando um card for criado → definir Ana como responsável',
        'Quando um card for criado → adicionar a etiqueta bug',
        'Quando o SLA estourar → avisar quem criou e o responsável',
    ]
    for rule in rules:
        rule.full_clean()


@pytest.mark.parametrize(
    ('data', 'message'),
    [
        ({'trigger': 'entered_column', 'action': 'notify'}, 'coluna do gatilho'),
        ({'trigger': 'created', 'action': 'move'}, 'coluna de destino'),
        ({'trigger': 'created', 'action': 'assign'}, 'responsável'),
        ({'trigger': 'created', 'action': 'add_label'}, 'etiqueta'),
        (
            {'trigger': 'entered_column', 'trigger_column': 'qa', 'action': 'move', 'action_column': 'qa'},
            'mesma coluna',
        ),
    ],
)
def test_validacao(loja, data, message):
    with pytest.raises(ValidationError, match=message):
        build(loja, **data).full_clean()


def test_etiqueta_de_outro_projeto_e_recusada(loja):
    from hubflow.projects.models import Project

    other = Project.objects.create(client=loja.client, name='Outro', owner='acme', repo='outro')
    label = Label.objects.create(project=other, name='bug')

    with pytest.raises(ValidationError, match='deste projeto'):
        build(loja, trigger='created', action='add_label', action_label=label).full_clean()


def test_ligada_por_padrao_e_uuid7(loja):
    rule = Automation.objects.create(project=loja, name='Regra', trigger='created', action='notify')

    assert rule.is_active and rule.uuid.version == 7
    assert list(loja.automations.all()) == [rule]
