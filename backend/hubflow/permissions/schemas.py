from datetime import datetime
from uuid import UUID

from ninja import Schema


class ClientBriefOut(Schema):
    id: int
    name: str


class UserAccessOut(Schema):
    # Dicionário montado por describe_user (sem resolvers de UserOut, que leem o objeto).
    id: int
    uuid: UUID
    email: str
    name: str
    first_name: str
    avatar_url: str | None
    is_active: bool
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
    extra_permissions: list[str]
    clients: list[ClientBriefOut]


class InviteIn(Schema):
    email: str
    name: str = ''
    roles: list[str] = []
    client_ids: list[int] = []


class RolesIn(Schema):
    roles: list[str]


class PermissionsIn(Schema):
    permissions: list[str]


class ClientsIn(Schema):
    client_ids: list[int]


class ActiveIn(Schema):
    is_active: bool


class RoleOut(Schema):
    name: str
    permissions: list[str]


class PermissionOut(Schema):
    code: str
    label: str


class CatalogOut(Schema):
    roles: list[RoleOut]
    permissions: list[PermissionOut]


class PermissionChangeOut(Schema):
    id: int
    uuid: UUID
    created: datetime
    user: str
    changed_by: str | None
    action: str
    action_label: str
    before: list
    after: list

    @staticmethod
    def resolve_user(obj):
        return obj.user.email

    @staticmethod
    def resolve_changed_by(obj):
        return obj.created_by.email if obj.created_by else None

    @staticmethod
    def resolve_action_label(obj):
        return obj.get_action_display()
