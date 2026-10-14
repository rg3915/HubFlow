from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'provider', 'owner', 'repo', 'is_active')
    list_filter = ('provider', 'is_active', 'client')
    search_fields = ('name', 'owner', 'repo')
