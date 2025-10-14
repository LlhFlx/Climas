from django.contrib import admin
from .models import ExpressionTeamMember, ExpressionInvestigatorThematicAntecedent, InvestigatorCondition


class InvestigatorThematicAxisAntecedentInline(admin.TabularInline):
    model = ExpressionInvestigatorThematicAntecedent
    extra = 1
    fields = ('thematic_axis', 'description', 'evidence_url')
    verbose_name = "Antecedente"
    verbose_name_plural = "Antecedentes en Ejes Temáticos"


class InvestigatorConditionInline(admin.TabularInline):
    model = InvestigatorCondition
    extra = 1
    fields = ('condition_text', 'is_fulfilled', 'fulfillment_date')
    verbose_name = "Condición"
    verbose_name_plural = "Condiciones de Participación"


@admin.register(ExpressionTeamMember)
class ProjectTeamMemberAdmin(admin.ModelAdmin):
    list_display = ('person', 'role', 'expression', 'status', 'start_date', 'end_date')
    list_filter = ('role', 'status', 'expression__call', 'start_date')
    search_fields = (
        'person__first_name',
        'person__first_last_name',
        'person__second_last_name',
        'expression__project_title'
    )
    autocomplete_fields = ('expression', 'person')
    inlines = [InvestigatorThematicAxisAntecedentInline, InvestigatorConditionInline]

    fieldsets = (
        (None, {
            'fields': ('expression', 'person', 'role', 'status')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(ExpressionInvestigatorThematicAntecedent)
class InvestigatorThematicAxisAntecedentAdmin(admin.ModelAdmin):
    list_display = ('team_member', 'thematic_axis', 'description')
    list_filter = ('thematic_axis', 'team_member__expression__call')
    search_fields = ('description', 'team_member__person__first_name')


@admin.register(InvestigatorCondition)
class InvestigatorConditionAdmin(admin.ModelAdmin):
    list_display = ('team_member', 'is_fulfilled', 'fulfillment_date')
    list_filter = ('is_fulfilled', 'team_member__expression__call')
    search_fields = ('condition_text',)