from .catalog import PERMISSIONS


def effective_permissions(user):
    """Codinomes do catálogo que a pessoa tem, somando papéis (grupos) e permissões por pessoa."""
    if user.is_superuser:
        return set(PERMISSIONS)
    granted = {perm.split('.', 1)[1] for perm in user.get_all_permissions() if perm.startswith('permissions.')}
    return granted & set(PERMISSIONS)


def has_perm(user, codename):
    return codename in effective_permissions(user)
