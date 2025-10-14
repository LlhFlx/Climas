from django.contrib import admin
from .models import Status

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'color', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('UI Settings', {
            'fields': ('color',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        })
    )

    ordering = ['name']
