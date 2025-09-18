from django.contrib import admin
from .models import CBO, CBOAntecedent, CBORelevantRole


class CBOAntecedentInline(admin.TabularInline):
    model = CBOAntecedent
    extra = 1
    fields = ('project_name', 'year', 'funding_source', 'outcomes')
    verbose_name = "Antecedente"
    verbose_name_plural = "Antecedentes de la CBO"


class CBORelevantRoleInline(admin.TabularInline):
    model = CBORelevantRole
    extra = 1
    fields = ('predefined_role', 'custom_role', 'person_name', 'contact_phone', 'contact_email')
    verbose_name = "Rol Relevante"
    verbose_name_plural = "Roles Relevantes en la CBO"

    def formfield_for_choice_field(self, db, request, **kwargs):
        # Optional: Improve UX by showing both predefined and custom
        return super().formfield_for_choice_field(db, request, **kwargs)


@admin.register(CBO)
class CBOAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number_of_members',
        'contact_person_name',
        'contact_phone',
        'contact_email',
        'created_at'
    )
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'contact_person_name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'number_of_members')
        }),
        ('Contacto', {
            'fields': ('contact_person_name', 'contact_phone', 'contact_email')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [CBOAntecedentInline, CBORelevantRoleInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make custom_role optional if predefined_role is selected
        return form