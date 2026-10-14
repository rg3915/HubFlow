from ninja.security import HttpBearer

from hubflow.permissions.services import has_perm

from .models import Token


class TokenAuth(HttpBearer):
    # RN-06: toda rota exige token, salvo as marcadas com auth=None.
    def authenticate(self, request, key):
        token = Token.objects.select_related('user').filter(key=key, user__is_active=True).first()
        if token is None or (token.is_cli and not has_perm(token.user, 'permissions.use_cli')):
            return None  # token da CLI deixa de valer se a permissão for retirada
        request.user = token.user
        request.token = token
        return token.user
