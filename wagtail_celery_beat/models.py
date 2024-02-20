from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class PermissionOnlyModel(models.Model):
    class Meta:
        verbose_name = _("Wagtail Celery Beat Permission")
        verbose_name_plural = _("Wagtail Celery Beat Permissions")

        managed = False
        default_permissions = ()
        permissions = (
            ("run_periodic_task", _("Can run periodic tasks")),
            ("toggle_periodic_task", _("Can toggle periodic tasks")),
            ("enable_periodic_task", _("Can enable periodic tasks")),
            ("disable_periodic_task", _("Can disable periodic tasks")),
        )