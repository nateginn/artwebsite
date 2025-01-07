# acceleratedrehabtherapy/apps/main/admin.py
from django.contrib import admin
from .models import MainPageConfig


@admin.register(MainPageConfig)
class MainPageConfigAdmin(admin.ModelAdmin):
    list_display = ['title', 'updated']
    search_fields = ['title', 'description']
    readonly_fields = ['created', 'updated']
    fieldsets = [
        (None, {
            'fields': ['title', 'description']
        }),
        ('Content', {
            'fields': ['text', 'background']
        }),
        ('Metadata', {
            'fields': ['created', 'updated'],
            'classes': ['collapse']
        })
    ]
