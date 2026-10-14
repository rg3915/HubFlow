import secrets

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from hubflow.core.models import TimeStampedModel, UuidModel

from .managers import UserManager


class User(UuidModel, TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('e-mail', unique=True)
    name = models.CharField('nome', max_length=150, blank=True)
    avatar = models.ImageField('avatar', upload_to='avatars/%Y/%m/', blank=True)
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('equipe', default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.email

    @property
    def first_name(self):
        return self.name.split()[0] if self.name.strip() else self.email.split('@')[0]

    def save(self, *args, **kwargs):
        # RN-01: e-mail guardado em minúsculas, o que torna o unique case-insensitive.
        self.email = self.email.lower()
        super().save(*args, **kwargs)


def generate_key():
    return secrets.token_hex(20)


class Token(UuidModel, TimeStampedModel):
    # RN-05: um token por dispositivo/CLI; o logout revoga só o token usado.
    key = models.CharField(max_length=40, unique=True, default=generate_key)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    is_cli = models.BooleanField(default=False)  # token aberto pela CLI (exige permissions.use_cli)

    def __str__(self):
        return f'{self.user} ({self.key[:6]}…)'
