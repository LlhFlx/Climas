from django.contrib import admin

# class MyAdminSite(AdminSite):
#     site_header = "Climas Admin"
#     site_title = "Climas Portal"
#     index_title = "Welcome to Climas Admin"
# admin.site = MyAdminSite(name='admin')

class CreatedByAdminMixin:
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


