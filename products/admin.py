from django.contrib import admin
from .models import ExpressionProduct
from core.admin import CreatedByAdminMixin

@admin.register(ExpressionProduct)
class ExpressionProductAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    list_display = (
        'title', 'expression', 'status', 'start_date', 'end_date', 'created_at'
    )
    list_filter = (
        'status', 'start_date', 'end_date', 'strategic_effects', 'created_at'
    )
    search_fields = (
        'title', 'description', 'outcome', 'expression__project_title'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('expression', 'strategic_effects', 'status')
    filter_horizontal = ('strategic_effects',)  # Nice UI for M2M

    fieldsets = (
        (None, {
            'fields': ('expression', 'title', 'description', 'outcome', 'status')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Efectos Estratégicos', {
            'fields': ('strategic_effects',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']