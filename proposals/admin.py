from django.contrib import admin
from core.admin import CreatedByAdminMixin


from django.contrib import admin
from .models import Proposal

# Register Proposal as separate model
@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['project_title', 'user', 'call', 'status', 'created_at']
    list_filter = ['call', 'status', 'created_at']
    search_fields = ['project_title', 'user__username', 'user__person__first_name']