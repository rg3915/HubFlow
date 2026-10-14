from django.contrib import admin

from .models import Milestone, Sprint


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'project', 'is_open', 'start_date', 'end_date')
    list_filter = ('is_open', 'project')


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'external_number', 'is_open')
    list_filter = ('is_open', 'project')
