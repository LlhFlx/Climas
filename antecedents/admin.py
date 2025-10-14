from django.contrib import admin
from .models import ProjectAntecedent

@admin.register(ProjectAntecedent)
class ProjectAntecedentAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'funding_amount', 'funding_source')
    list_filter = ('start_date', 'end_date', 'funding_source', 'institutions')
    search_fields = ('title', 'description', 'outcomes', 'institutions__name')
    autocomplete_fields = ('institutions',)
    filter_horizontal = ('institutions',)  # Nice UI for M2M

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'outcomes')
        }),
        ('Fechas y Financiamiento', {
            'fields': ('start_date', 'end_date', 'funding_amount', 'funding_source')
        }),
        ('Evidencia', {
            'fields': ('url',)
        }),
        ('Instituciones', {
            'fields': ('institutions',)
        }),
    )