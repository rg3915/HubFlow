import secrets

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        # RN-01: o login não diferencia maiúsculas.
        return self.get(email=email.lower())


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('e-mail', unique=True)
    name = models.CharField('nome', max_length=150, blank=True)
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('equipe', default=False)
    date_joined = models.DateTimeField('cadastrado em', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # RN-01: e-mail guardado em minúsculas, o que torna o unique case-insensitive.
        self.email = self.email.lower()
        super().save(*args, **kwargs)


def generate_key():
    return secrets.token_hex(20)


class Token(models.Model):
    # RN-05: um token por dispositivo/CLI; o logout revoga só o token usado.
    key = models.CharField(max_length=40, unique=True, default=generate_key)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} ({self.key[:6]}…)'
