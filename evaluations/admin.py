from django.contrib import admin
from .models import (
    EvaluationTemplate,
    TemplateCategory,
    TemplateSubcategory,
    TemplateItem,
    TemplateItemOption,
    Evaluation,
    EvaluationResponse,
)
from core.admin import CreatedByAdminMixin


class TemplateItemOptionInline(admin.TabularInline):
    model = TemplateItemOption
    extra = 1
    fields = ('display_text', 'score')
    verbose_name = "Opción"
    verbose_name_plural = "Opciones"

# Inline: Items dentro de Categoría
class TemplateItemInline(admin.TabularInline):
    model = TemplateItem
    extra = 1
    fields = ('question', 'field_type', 'max_score', 'order')
    verbose_name = "Ítem"
    verbose_name_plural = "Ítems"

class TemplateSubcategoryInline(admin.TabularInline):
    model = TemplateSubcategory
    extra = 1
    fields = ('name', 'order')
    verbose_name = "Subcategoría"
    verbose_name_plural = "Subcategorías"


# Inline: Categorías dentro de Plantilla
class TemplateCategoryInline(admin.TabularInline):
    model = TemplateCategory
    extra = 1
    fields = ('name', 'order')
    verbose_name = "Categoría"
    verbose_name_plural = "Categorías"


@admin.register(EvaluationTemplate)
class EvaluationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TemplateCategoryInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Aplicabilidad', {
            'fields': ('applies_to_expression', 'applies_to_proposal', 'calls'),
        }),
        ('Estado', {
            'fields': ('is_active',),
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['name']


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'order')
    list_filter = ('template',)
    search_fields = ('name',)
    autocomplete_fields = ('template',)
    inlines = [TemplateSubcategoryInline]
    ordering = ['template', 'order']

@admin.register(TemplateSubcategory)
class TemplateSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order')
    list_filter = ('category__template',)
    search_fields = ('name',)
    autocomplete_fields = ('category',)
    inlines = [TemplateItemInline]
    ordering = ['category', 'order']


@admin.register(TemplateItem)
class TemplateItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'subcategory', 'field_type', 'source_model', 'max_score', 'order')
    list_filter = ('field_type', 'subcategory__category__template')
    search_fields = ('question',)
    autocomplete_fields = ('subcategory',)
    readonly_fields = ('created_at', 'updated_at')

    def get_fieldsets(self, request, obj=None):
        # Start with basic fields
        basic_fields = ('subcategory', 'question', 'field_type', 'max_score', 'order')
        static_options_fields = ('options',)
        dynamic_options_fields = ('source_model',)

        fieldsets = [
            (None, {
                'fields': basic_fields
            }),
            ('Opciones Estáticas', {
                'fields': static_options_fields,
                'classes': ('collapse',),
                'description': 'Usar solo si no se usa un modelo de origen'
            }),
        ]

        # Only show dynamic options if field_type is dropdown or radio
        if obj and obj.field_type in ['dropdown', 'radio']:
            fieldsets.append((
                'Opciones Dinámicas', {
                    'fields': dynamic_options_fields,
                    'classes': ('collapse',),
                    'description': 'Si se selecciona, ignora las opciones estáticas'
                }
            ))
        elif not obj:
            # If obj is None (creating new), show it conditionally via JavaScript
            fieldsets.append((
                'Opciones Dinámicas', {
                    'fields': dynamic_options_fields,
                    'classes': ('collapse',),
                    'description': 'Solo para campos "dropdown" o "radio"'
                }
            ))

        # Always add audit at the end
        fieldsets.append((
            'Auditoría', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ))

        return fieldsets

    # fieldsets = (
    #     (None, {
    #         'fields': ('category', 'question', 'field_type', 'max_score', 'order')
    #     }),
    #     ('Opciones Estáticas', {
    #         'fields': ('options',),
    #         'classes': ('collapse',),
    #         'description': 'Usar solo si no se usa un modelo de origen'
    #     }),
    #     ('Opciones Dinámicas', {
    #         'fields': ('source_model',),
    #         'classes': ('collapse',),
    #         'description': 'Si se selecciona, ignora las opciones estáticas'
    #     }),
    #     ('Auditoría', {
    #         'fields': ('created_at', 'updated_at'),
    #         'classes': ('collapse',)
    #     }),
    # )

    #ordering = ['category', 'order']


@admin.register(Evaluation)
class EvaluationAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    list_display = (
        'target_display',
        'evaluator',
        'status',
        'total_score',
        'submission_datetime',
        'created_at'
    )
    list_filter = (
        'status',
        'evaluator',
        'submission_datetime',
        'created_at',
        'template',
        'target_content_type',
    )
    search_fields = (
        'evaluator__username',
        'evaluator__person__first_name',
        'evaluator__person__first_last_name',
        'target_object_id',
    )
    readonly_fields = ('created_at', 'updated_at', 'total_score', 'max_possible_score')
    autocomplete_fields = ('evaluator', 'status', 'template')
    date_hierarchy = 'submission_datetime'

    fieldsets = (
        (None, {
            'fields': ('target_content_type', 'target_object_id', 'evaluator', 'status', 'template')
        }),
        ('Resultados', {
            'fields': ('total_score', 'max_possible_score')
        }),
        ('Control', {
            'fields': ('is_positive', 'is_validated', 'coordinator_notes')
        }),
        ('Envío', {
            'fields': ('submission_datetime',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-submission_datetime']

    def target_display(self, obj):
        """Custom column showing Expression or Proposal title."""
        if obj.target_content_type.model == "expression":
            return getattr(obj.target, "project_title", f"Expresión {obj.target_object_id}")
        elif obj.target_content_type.model == "proposal":
            return getattr(obj.target, "title", f"Propuesta {obj.target_object_id}")
        return f"Objetivo {obj.target_object_id}"
    target_display.short_description = "Objetivo"


@admin.register(EvaluationResponse)
class EvaluationResponseAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'item', 'score', 'created_at')
    list_filter = (
        'created_at',
        'evaluation__evaluator',
        'item__subcategory__category__template',
        'item__field_type'
    )
    search_fields = (
        'value',
        'comment',
        'item__question',
        'evaluation__evaluator__username'
    )
    autocomplete_fields = ('evaluation', 'item')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('evaluation', 'item')
        }),
        ('Respuesta', {
            'fields': ('value', 'score', 'comment')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'evaluation',
            'item',
            'item__subcategory__category',
            'evaluation__evaluator'
        )

    ordering = ['-created_at']
   

# from django.contrib import admin
# from .models import Evaluation, EvaluationCategory, EvaluationItem, EvaluationResponse
# #from core.admin import CreatedByAdminMixin


# # Inline: Items dentro de Categoría
# class EvaluationItemInline(admin.TabularInline):
#     model = EvaluationItem
#     extra = 1
#     fields = ('question', 'max_score', 'help_text', 'order')
#     verbose_name = "Ítem"
#     verbose_name_plural = "Ítems"


# # Inline: Categorías dentro de Evaluación
# class EvaluationCategoryInline(admin.TabularInline):
#     model = EvaluationCategory
#     extra = 1
#     fields = ('name', 'weight', 'order')
#     verbose_name = "Categoría"
#     verbose_name_plural = "Categorías"
#     inlines = [EvaluationItemInline]


# # # Inline: Respuestas en Evaluación (opcional para vista rápida)
# # class EvaluationResponseInline(admin.TabularInline):
# #     model = EvaluationResponse
# #     extra = 0
# #     fields = ('item', 'score', 'comment', 'evaluator')
# #     readonly_fields = ('evaluator', 'created_at', 'updated_at')
# #     verbose_name = "Respuesta"
# #     verbose_name_plural = "Respuestas"
# #     can_delete = False

# #     def has_add_permission(self, request, obj):
# #         return False


# @admin.register(Evaluation)
# class EvaluationAdmin(admin.ModelAdmin):
#     list_display = (
#         'expression',
#         'evaluator',
#         'status',
#         'total_score',
#         'submission_datetime',
#         'created_at'
#     )
#     list_filter = (
#         'status',
#         'evaluator',
#         'submission_datetime',
#         'created_at',
#         'expression__call'
#     )
#     search_fields = (
#         'expression__project_title',
#         'expression__user__first_name',
#         'expression__user__first_last_name',
#         'evaluator__username'
#     )
#     readonly_fields = ('created_at', 'updated_at', 'total_score', 'max_possible_score')
#     autocomplete_fields = ('expression', 'evaluator', 'status')
#     date_hierarchy = 'submission_datetime'

#     fieldsets = (
#         (None, {
#             'fields': ('expression', 'evaluator', 'status')
#         }),
#         ('Resultados', {
#             'fields': ('total_score', 'max_possible_score')
#         }),
#         ('Envío', {
#             'fields': ('submission_datetime',)
#         }),
#         ('Auditoría', {
#             'fields': ('created_by', 'created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )

#     inlines = [EvaluationCategoryInline]#, EvaluationResponseInline]
#     ordering = ['-submission_datetime']


# @admin.register(EvaluationCategory)
# class EvaluationCategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'evaluation', 'weight', 'order')
#     list_filter = ('evaluation__expression__call', 'evaluation__evaluator')
#     search_fields = ('name', 'evaluation__expression__project_title')
#     autocomplete_fields = ('evaluation',)
#     inlines = [EvaluationItemInline]


# @admin.register(EvaluationItem)
# class EvaluationItemAdmin(admin.ModelAdmin):
#     list_display = ('question', 'category', 'max_score', 'order')
#     list_filter = ('category__evaluation__expression__call',)
#     search_fields = ('question', 'category__name')
#     autocomplete_fields = ('category',)


# @admin.register(EvaluationResponse)
# class EvaluationResponseAdmin(admin.ModelAdmin):
#     list_display = ('item', 'evaluator', 'score', 'created_at')
#     list_filter = ('created_at', 'evaluator', 'item__category__evaluation__expression__call')
#     search_fields = ('comment', 'item__question', 'evaluator__username')
#     autocomplete_fields = ('item', 'evaluator')
#     readonly_fields = ('created_at', 'updated_at')

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related(
#             'item', 'item__category', 'evaluator'
#         )

# # from django.contrib import admin
# # from .models import Evaluation

# # @admin.register(Evaluation)
# # class EvaluationAdmin(CreatedByAdminMixin, admin.ModelAdmin):
# #     list_display = (
# #         'expression', 'evaluator', 'overall_score', 'status',
# #         'evaluation_datetime'
# #     )
# #     list_filter = ('status', 'evaluator', 'evaluation_datetime', 'overall_score')
# #     search_fields = (
# #         'expression__project_title',
# #         'evaluator__username',
# #         'comments'
# #     )
# #     readonly_fields = ('created_at', 'updated_at', 'evaluation_datetime')
# #     autocomplete_fields = ('expression', 'evaluator', 'status')
# #     fieldsets = (
# #         (None, {
# #             'fields': ('expression', 'evaluator', 'status')
# #         }),
# #         ('Puntuaciones', {
# #             'fields': ('overall_score', 'technical_score', 'feasibility_score', 'relevance_score')
# #         }),
# #         ('Contenido', {
# #             'fields': ('comments', 'recommendation')
# #         }),
# #         ('Auditoría', {
# #             'fields': ('created_by', 'created_at', 'updated_at'),
# #             'classes': ('collapse',)
# #         }),
# #     )

# #     def save_model(self, request, obj, form, change):
# #         if not change:
# #             obj.created_by = request.user
# #         super().save_model(request, obj, form, change)