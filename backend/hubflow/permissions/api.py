from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.clients.models import Client

from .catalog import ALL, LABELS, ROLES
from .models import Membership
from .schemas import ActiveIn, CatalogOut, ClientsIn, PermissionsIn, RolesIn, UserAccessOut
from .services import describe_user, require, users_with_access

router = Router(tags=['users'])
MANAGE = 'accounts.change_user'


def managed_user(request, user_id):
    require(request.user, MANAGE)
    return get_object_or_404(users_with_access(), id=user_id)


def fresh(user_id):
    return describe_user(users_with_access().get(id=user_id))


@router.get('/users/manage', response=list[UserAccessOut])
def list_users_access(request):
    require(request.user, MANAGE)
    return [describe_user(user) for user in users_with_access()]


@router.get('/users/catalog', response=CatalogOut)
def catalog(request):
    require(request.user, MANAGE)
    return {
        'roles': [{'name': name, 'permissions': perms} for name, perms in ROLES.items()],
        'permissions': [{'code': code, 'label': label} for code, label in LABELS.items()],
    }


@router.put('/users/{user_id}/roles', response={200: UserAccessOut, 400: DetailOut})
def set_roles(request, user_id: int, data: RolesIn):
    user = managed_user(request, user_id)
    unknown = [name for name in data.roles if name not in ROLES]
    if unknown:
        return Status(400, {'detail': f'Papel desconhecido: {", ".join(unknown)}.'})
    user.groups.set(Group.objects.filter(name__in=data.roles))
    return fresh(user.id)


@router.put('/users/{user_id}/permissions', response={200: UserAccessOut, 400: DetailOut})
def set_permissions(request, user_id: int, data: PermissionsIn):
    user = managed_user(request, user_id)
    unknown = [code for code in data.permissions if code not in ALL]
    if unknown:
        return Status(400, {'detail': f'Permissão fora do catálogo: {", ".join(unknown)}.'})
    wanted = [
        Permission.objects.get(content_type__app_label=app, codename=name)
        for app, name in (c.split('.') for c in data.permissions)
    ]
    user.user_permissions.set(wanted)
    return fresh(user.id)


@router.put('/users/{user_id}/clients', response=UserAccessOut)
def set_clients(request, user_id: int, data: ClientsIn):
    user = managed_user(request, user_id)
    clients = Client.objects.filter(id__in=data.client_ids)
    Membership.objects.filter(user=user).exclude(client__in=clients).delete()
    for client in clients:
        Membership.objects.get_or_create(user=user, client=client)
    return fresh(user.id)


@router.put('/users/{user_id}/active', response={200: UserAccessOut, 400: DetailOut})
def set_active(request, user_id: int, data: ActiveIn):
    user = managed_user(request, user_id)
    if user.id == request.user.id and not data.is_active:
        return Status(400, {'detail': 'Você não pode desativar a própria conta.'})
    user.is_active = data.is_active
    user.save(update_fields=['is_active'])
    return fresh(user.id)
