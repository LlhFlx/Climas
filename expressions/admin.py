from django.contrib import admin
from expressions.models import Expression
from core.admin import CreatedByAdminMixin

@admin.register(Expression)
class ExpressionAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    list_display = ('project_title', 'user', 'call', 'status', 'submission_datetime')
    list_filter = ('status', 'call', 'thematic_axis', 'submission_datetime')
    search_fields = ('project_title', 'problem', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'submission_datetime')
    autocomplete_fields = ('user', 'call', 'thematic_axis', 'status', 'implementation_country')
