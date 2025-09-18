from django.contrib import admin
from .models import ExperienceType, ProjectLeaderExperience


@admin.register(ExperienceType)
class ExperienceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProjectLeaderExperience)
class ProjectLeaderExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'expression', 'experience_type', 'academic_title', 'current_position')
    list_filter = ('experience_type', 'academic_title', 'current_position', 'expression__call')
    search_fields = (
        'user__person__first_name',
        'user__person__first_last_name',
        'expression__project_title'
    )
    autocomplete_fields = ('expression', 'user', 'experience_type')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('expression', 'user', 'experience_type')
        }),
        ('Detalles del Líder', {
            'fields': ('academic_title', 'current_position')
        }),
        ('Experiencia', {
            'fields': ('description',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )