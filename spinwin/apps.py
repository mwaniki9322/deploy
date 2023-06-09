from django.apps import AppConfig


class SpinwinConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spinwin'

    def ready(self):
        import spinwin.signals
