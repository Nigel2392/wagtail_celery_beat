from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailCeleryBeatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wagtail_celery_beat'
