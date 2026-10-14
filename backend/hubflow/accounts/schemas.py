from uuid import UUID

from ninja import ModelSchema, Schema

from .models import User


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    token: str


class UserOut(ModelSchema):
    first_name: str
    avatar_url: str | None

    class Meta:
        model = User
        fields = ['id', 'uuid', 'email', 'name']

    @staticmethod
    def resolve_avatar_url(user):
        return user.avatar.url if user.avatar else None


class ForgotPasswordIn(Schema):
    email: str


class DetailOut(Schema):
    detail: str


class ResetPasswordIn(Schema):
    uid: str
    token: str
    password: str


class ChangePasswordIn(Schema):
    current_password: str
    new_password: str


class MeOut(Schema):
    """Montado a partir de um dicionário (sem os resolvers do UserOut)."""

    id: int
    uuid: UUID
    email: str
    name: str
    first_name: str
    avatar_url: str | None
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
