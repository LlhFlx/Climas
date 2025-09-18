from django.contrib import admin
from .models import BudgetCategory, BudgetPeriod, BudgetItem
from core.admin import CreatedByAdminMixin

@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Prevent adding new categories in admin
        #return super().has_add_permission(request)
        return False
    
    def has_delete_permission(self, request, obj = ...):
        return False
    
    def changeform_view(self, request, object_id = ..., form_url = ..., extra_context = ...):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)
    
@admin.register(BudgetPeriod)
class BudgetPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_filter = ('order',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'order')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('expression', 'category', 'period', 'amount', 'created_at')
    list_filter = ('category', 'period', 'expression__call', 'created_at')
    search_fields = ('expression__project_title', 'notes')
    autocomplete_fields = ('expression', 'category', 'period')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('expression', 'category', 'period', 'amount')
        }),
        ('Detalles', {
            'fields': ('notes',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )