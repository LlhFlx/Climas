from django.contrib import admin
from .models import Call

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'coordinator', 'opening_datetime', 'closing_datetime')
    list_filter = ('status', 'coordinator', 'opening_datetime', 'closing_datetime', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('coordinator', 'status', 'created_by')
    date_hierarchy = 'opening_datetime'
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status', 'coordinator')
        }),
        ('Fechas', {
            'fields': ('opening_datetime', 'closing_datetime'),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    ordering = ['-opening_datetime']
    # formfield_overrides = {
    #     models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 3})},
    # }
