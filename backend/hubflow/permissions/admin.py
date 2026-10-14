from django.contrib import admin

from .models import Membership, PermissionChange


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'client', 'created')
    list_filter = ('client',)


@admin.register(PermissionChange)
class PermissionChangeAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'action', 'created_by')
    list_filter = ('action',)
    readonly_fields = ('user', 'action', 'before', 'after', 'created_by')
