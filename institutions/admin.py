from django.contrib import admin
from .models import InstitutionType, Institution

@admin.register(InstitutionType)
class InstitutionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'institution_type', 'country', 'is_active')
    list_filter = ('institution_type', 'is_active', 'country', 'created_at')
    search_fields = ('name', 'acronym', 'tax_register_number')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('legal_representative', 'administrative_representative', 'created_by', 'country')
    fieldsets = (
        (None, {
            'fields': ('name', 'acronym', 'institution_type', 'is_active', 'country')
        }),
        ('Representatives', {
            'fields': ('legal_representative', 'administrative_representative')
        }),
        ('Contact & Tax', {
            'fields': ('website', 'tax_register_number')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state'),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    ordering = ['name']
