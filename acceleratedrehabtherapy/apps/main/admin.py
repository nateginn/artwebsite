# acceleratedrehabtherapy/apps/main/admin.py
from django.contrib import admin
from .models import MainPageConfig, LandingPageLead


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


@admin.register(LandingPageLead)
class LandingPageLeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'preferred_location', 'source_page', 'created']
    list_filter = ['source_page', 'preferred_location', 'created']
    search_fields = ['name', 'email', 'phone', 'condition']
    readonly_fields = ['created']
    ordering = ['-created']
    fieldsets = [
        (None, {
            'fields': ['name', 'phone', 'email', 'condition', 'preferred_location']
        }),
        ('Source', {
            'fields': ['source_page', 'created'],
        }),
    ]
