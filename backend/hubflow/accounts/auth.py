from ninja.security import HttpBearer

from .models import Token


class TokenAuth(HttpBearer):
    # RN-06: toda rota exige token, salvo as marcadas com auth=None.
    def authenticate(self, request, key):
        token = Token.objects.select_related('user').filter(key=key, user__is_active=True).first()
        if token is None:
            return None
        request.user = token.user
        request.token = token
        return token.user
