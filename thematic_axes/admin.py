from django.contrib import admin
from .models import ThematicAxis

@admin.register(ThematicAxis)
class ThematicAxisAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
