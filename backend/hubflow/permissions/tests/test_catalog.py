import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError

from hubflow.clients.models import Client
from hubflow.permissions.catalog import ALL, CUSTOM_PERMISSIONS, LABELS, ROLES
from hubflow.permissions.models import Membership
from hubflow.permissions.services import effective_permissions, has_perm

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_so_duas_permissoes_sao_especificas():
    # O resto usa add/change/delete/view padrão do Django.
    assert set(CUSTOM_PERMISSIONS) == {'use_cli', 'view_own_payments'}
    assert all(p.count('.') == 1 for p in ALL)
    assert 'boards.change_card' in ALL and 'billing.view_payment' in ALL


def test_todas_as_permissoes_do_catalogo_existem_no_banco():
    for perm in ALL:
        app, codename = perm.split('.')
        assert Permission.objects.filter(content_type__app_label=app, codename=codename).exists(), perm


def test_papeis_padrao_existem_com_as_permissoes_certas():
    assert set(ROLES) == {'Administrador', 'Gerente', 'Desenvolvedor', 'Financeiro', 'Cliente', 'Leitura'}
    for name, perms in ROLES.items():
        group = Group.objects.get(name=name)
        granted = {
            f'{p.content_type.app_label}.{p.codename}' for p in group.permissions.select_related('content_type')
        }
        assert granted == set(perms), name
    assert set(ROLES['Administrador']) == set(ALL)
    assert 'permissions.use_cli' in ROLES['Desenvolvedor'] and 'billing.view_payment' not in ROLES['Desenvolvedor']
    assert ROLES['Cliente'] == ['permissions.view_own_payments']


def test_permissoes_efetivas_vem_do_papel_e_da_pessoa():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    user.groups.add(Group.objects.get(name='Desenvolvedor'))
    user.user_permissions.add(Permission.objects.get(content_type__app_label='billing', codename='view_payment'))

    perms = effective_permissions(user)

    assert 'boards.add_card' in perms and 'billing.view_payment' in perms and 'accounts.change_user' not in perms
    assert has_perm(user, 'permissions.use_cli') is True
    assert has_perm(user, 'boards.change_card') is False


def test_superusuario_tem_tudo():
    admin = User.objects.create_superuser(email='admin@hubflow.com', password='x')

    assert effective_permissions(admin) == set(ALL)


def test_rotulos_em_portugues_para_a_tela():
    assert LABELS['boards.change_card'] == 'Editar e mover qualquer card'
    assert set(LABELS) == set(ALL)


def test_vinculo_usuario_cliente_e_unico():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    acme = Client.objects.create(name='ACME')
    Membership.objects.create(user=user, client=acme)

    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, client=acme)


def test_clientes_da_pessoa():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    acme = Client.objects.create(name='ACME')
    Client.objects.create(name='Beta')
    Membership.objects.create(user=user, client=acme)

    assert list(user.memberships.values_list('client__name', flat=True)) == ['ACME']
