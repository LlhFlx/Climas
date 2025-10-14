from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    # Trigger signal at: common/management/commands/load_base_data.py
    def ready(self):
        from django.db.models.signals import post_migrate
        from .management.commands.load_base_data import Command as LoadBaseData

        def load_initial_data(sender, **kwargs):
            LoadBaseData().handle()

        post_migrate.connect(load_initial_data, sender=self)