from django.apps import AppConfig
from django.contrib.admin import AdminSite


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'


    def ready(self):
        # Import here to avoid app-loading-time side effects
        from django.contrib import admin

        # Customize admin site
        AdminSite.site_header = "Climas Admin"
        AdminSite.site_title = "Climas Portal"
        AdminSite.index_title = "Welcome to Climas Admin"

        # Custom class
        # class MyAdminSite(AdminSite):
        #     site_header = "Climas Admin"
        #     site_title = "Climas Portal"
        #     index_title = "Welcome to Climas Admin"
        #
        # admin.site = MyAdminSite(name='admin')