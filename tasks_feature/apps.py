from django.apps import AppConfig


class TasksFeatureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks_feature'

    def ready(self):
        import tasks_feature.signals
