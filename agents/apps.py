from django.apps import AppConfig


class NeoCreativeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agents'

    def ready(self):
        import agents.signals
