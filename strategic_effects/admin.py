from django.contrib import admin
from .models import StrategicEffect
from core.admin import CreatedByAdminMixin

@admin.register(StrategicEffect)
class StrategicEffectAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['name']