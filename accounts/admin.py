# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth import get_user_model
# from .models import Role, CustomUser

# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'is_active', 'created_at')
#     list_filter = ['is_active']
#     seach_fields = ('name', 'description')

# #admin.site.unregister(User)

# @admin.register(CustomUser)
# class UserAdmin(BaseUserAdmin):
#     # Add 'person' to display
#     list_display = BaseUserAdmin.list_display + ('email', 'role', 'person')
#     list_select_related = ('person', 'role')

#     search_fields = (*BaseUserAdmin.search_fields, 'email', 'person__first_name', 'person__first_last_name')
#     list_filter = (*BaseUserAdmin.list_filter, 'role', 'user__is_staff')

#     # Allow filtering by person
#     autocomplete_fields = ('person',)

#     # Keep original fieldsets
#     fieldsets = BaseUserAdmin.fieldsets + (
#         ('Profile', {'fields': ('person',)}),
#     )

#     fieldsets = (
#         (None, {'fields': ('user__username', 'user__password')}),
#         ('Personal Info', {'fields': ('email',)}),
#         ('Permissions', {'fields': ('user__is_active', 'user__is_staff', 'user.is_superuser', 'user__groups', 'user__user_permissions')}),
#         ('Important Dates', {'fields': ('user__last_login', 'user__date_joined')}),
#         ('Profile', {'fields': ('person', 'role', 'birthdate', 'phone_number')}),
#     )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Role, CustomUser

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ['is_active']
    search_fields = ('name', 'description')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):  # Changed from BaseUserAdmin to ModelAdmin
    # Display fields - using methods for related User fields
    list_display = ('get_username', 'email', 'role', 'person', 'birthdate', 'phone_number', 'get_is_staff', 'get_is_active')
    list_select_related = ('person', 'role', 'user')
    search_fields = ('user__username', 'email', 'person__first_name', 'person__last_name')
    list_filter = ('role', 'user__is_staff', 'user__is_active')
    autocomplete_fields = ('person',)
    
    # Custom fieldsets for CustomUser
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Personal Info', {'fields': ('email', 'birthdate', 'phone_number')}),
        ('Profile', {'fields': ('person', 'role')}),
    )
    
    # Methods to display related User fields
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'
    
    def get_is_staff(self, obj):
        return obj.user.is_staff
    get_is_staff.boolean = True
    get_is_staff.short_description = 'Staff'
    get_is_staff.admin_order_field = 'user__is_staff'
    
    def get_is_active(self, obj):
        return obj.user.is_active
    get_is_active.boolean = True
    get_is_active.short_description = 'Active'
    get_is_active.admin_order_field = 'user__is_active'
    
    # Ordering based on email
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
