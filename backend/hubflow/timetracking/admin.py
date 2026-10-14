from django.contrib import admin

from .models import TimeEntry


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('card', 'user', 'started_at', 'ended_at', 'is_manual')
    list_filter = ('is_manual', 'user')
    date_hierarchy = 'started_at'
