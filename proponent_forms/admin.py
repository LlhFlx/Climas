from django.contrib import admin
from .models import SharedQuestion, ProponentForm, ProponentFormQuestion, ProponentResponse


@admin.register(SharedQuestion)
class SharedQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'target_category', 'field_type', 'is_active')
    list_filter = ('target_category', 'field_type', 'is_active')
    search_fields = ('question',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('question', 'target_category', 'is_required', 'is_active')
        }),
        ('Tipo de Campo', {
            'fields': ('field_type',)
        }),
        ('Opciones Estáticas', {
            'fields': ('options',),
            'classes': ('collapse',),
            'description': 'Usar solo si no se usa un modelo de origen'
        }),
        ('Opciones Dinámicas', {
            'fields': ('source_model',),
            'classes': ('collapse',),
            'description': 'Si se selecciona, ignora las opciones estáticas'
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields
        return self.readonly_fields + ('target_category',)  # Prevent changing target after creation


class ProponentFormQuestionInline(admin.TabularInline):
    model = ProponentFormQuestion
    extra = 1
    fields = ('shared_question', 'order')
    autocomplete_fields = ('shared_question',)


@admin.register(ProponentForm)
class ProponentFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'call', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'call__title')
    autocomplete_fields = ('call',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProponentFormQuestionInline]

    fieldsets = (
        (None, {
            'fields': ('call', 'title', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProponentResponse)
class ProponentResponseAdmin(admin.ModelAdmin):
    list_display = ('expression', 'shared_question', 'value', 'created_at')
    list_filter = ('created_at', 'expression__call', 'shared_question__target_category')
    search_fields = ('value', 'comment', 'expression__project_title')
    autocomplete_fields = ('expression', 'shared_question')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('expression', 'shared_question')
        }),
        ('Respuesta', {
            'fields': ('value', 'comment')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )