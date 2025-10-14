from django.contrib import admin
from .models import Person
from core.admin import CreatedByAdminMixin

# @admin.register(Person)
# class PersonAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         if not change:
#             obj.created_by = request.user
#         super().save_model(request, obj, form, change)



@admin.register(Person)
class PersonAdmin(CreatedByAdminMixin, admin.ModelAdmin):

    def has_user_account(self, obj):
        return hasattr(obj, 'user_account') and obj.user_account is not None

    has_user_account.boolean = True
    has_user_account.short_description = "Tiene cuenta?"

    def user_email(self, obj):
        return obj.user_account.email if self.has_user_account(obj) else "-"
    
    user_email.short_description = "Email (Usuario)"
    user_email.admin_order_field = 'user_account__email'

    list_display = ('first_name', 'first_last_name', 'document_type', 'created_by', 'created_at')
    list_filter = ('document_type', 'created_at', 'created_by')
    search_fields = ('first_name', 'first_last_name', 'document_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Info', {
            'fields': ('first_name', 'second_name', 'first_last_name', 'second_last_name', 'gender')
        }),
        ('Document', {
            'fields': ('document_type', 'document_number')
        }),
        # ('Contact', {
        #     'fields': ('email', 'phone_number')
        # }),
        # ('Address', {
        #     'fields': ('address_line1', 'address_line2', 'city', 'state', 'country'),
        #     'classes': ('collapse',),
        # }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    autocomplete_fields = ('document_type', 'created_by')
    ordering = ['first_last_name', 'first_name']