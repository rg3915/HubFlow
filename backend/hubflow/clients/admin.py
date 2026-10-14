from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'modified')
    list_filter = ('is_active',)
    search_fields = ('name',)
