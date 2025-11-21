from django.apps import AppConfig


class AccommodationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accommodation'

    # def ready(self):
    #     from .dynamodb_helper import ensure_all_tables
    #     ensure_all_tables()