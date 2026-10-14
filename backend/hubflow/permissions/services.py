from .catalog import ALL


def effective_permissions(user):
    """Permissões 'app.codename' do catálogo que a pessoa tem (papéis + por pessoa); superusuário tem todas."""
    if user.is_superuser:
        return set(ALL)
    return user.get_all_permissions() & set(ALL)


def has_perm(user, perm):
    """`perm` no formato 'app.codename' (ex.: 'boards.change_card')."""
    return perm in effective_permissions(user)


def require(user, perm):
    """Levanta 403 com mensagem clara quando a pessoa não tem a permissão."""
    from ninja.errors import HttpError

    from .catalog import LABELS

    if not has_perm(user, perm):
        raise HttpError(403, f'Você não tem permissão para isto ({LABELS.get(perm, perm)}).')


def perm_code(permission):
    return f'{permission.content_type.app_label}.{permission.codename}'


def describe_user(user):
    """Papéis, permissões efetivas, permissões por pessoa e clientes, a partir dos relacionamentos já prefetchados."""
    roles = sorted(group.name for group in user.groups.all())
    from_roles = {perm_code(p) for group in user.groups.all() for p in group.permissions.all()}
    extra = sorted(perm_code(p) for p in user.user_permissions.all())
    effective = set(ALL) if user.is_superuser else (from_roles | set(extra)) & set(ALL)
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'first_name': user.first_name,
        'avatar_url': user.avatar.url if user.avatar else None,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'roles': roles,
        'permissions': sorted(effective),
        'extra_permissions': extra,
        'clients': [{'id': m.client_id, 'name': m.client.name} for m in user.memberships.all()],
    }


def users_with_access():
    from django.contrib.auth import get_user_model

    return (
        get_user_model()
        .objects.prefetch_related(
            'groups__permissions__content_type', 'user_permissions__content_type', 'memberships__client'
        )
        .order_by('email')
    )
