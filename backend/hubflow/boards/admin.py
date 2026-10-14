from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'project', 'column', 'position', 'modified')
    list_filter = ('column', 'project')
    search_fields = ('title', 'description')
