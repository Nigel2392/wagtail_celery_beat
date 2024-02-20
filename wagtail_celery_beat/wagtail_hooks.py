from django.utils.translation import gettext_lazy as _
from django.urls import include, path, reverse_lazy
from django.contrib.auth.models import Permission
from wagtail.admin.menu import MenuItem
from wagtail import hooks
from .admin import register_to_celery_menu
from .urls import urlpatterns as urls

HIDDEN_MAIN_MENU_ITEMS = [
    "clocked",
]

RENAMED_MAIN_MENU_ITEMS = {

}

# from django.conf import settings
# USING_CELERY_DB = getattr(settings, "USING_CELERY_DB", False)

# CELERY_BEAT_DB_APPS = [
#     "django_celery_beat",
#     "wagtail_celery_beat",
# ]

# @hooks.register("register_db_route")
# def register_db_route(model, **hints):
#     if model._meta.app_label in CELERY_BEAT_DB_APPS and USING_CELERY_DB:
#         return "celery_db"

class PermissionsMenuitem(MenuItem):
    permissions = None
    
    def __init__(self, *args, **kwargs):
        permissions = kwargs.pop("permissions", self.permissions)
        if isinstance(permissions, str):
            permissions = [permissions]
        self.permissions = permissions
        super().__init__(*args, **kwargs)

    def is_shown(self, request):
        if not super().is_shown(request):
            return False
        if self.permissions and not request.user.has_perms(self.permissions):
            return False
        return True

@hooks.register("construct_settings_menu")
def hide_items(request, menu_items: list):
    def item_filter(item):
        if item.name in HIDDEN_MAIN_MENU_ITEMS or item.__class__.__name__ in HIDDEN_MAIN_MENU_ITEMS:
            return None
        if item.name in RENAMED_MAIN_MENU_ITEMS:
            item.label = RENAMED_MAIN_MENU_ITEMS[item.name]
        return item
    menu_items[:] = filter(item_filter, menu_items)

@hooks.register("register_admin_urls")
def register_admin_urls():

    return [
        path("celery-admin/", include((urls, "wagtail_celery_beat"), namespace="wagtail_celery_beat")),
    ]


register_to_celery_menu(#SubmenuMenuItem(
    PermissionsMenuitem(
        label=_("Periodic Task Actions"),
        url=reverse_lazy("wagtail_celery_beat:index"),
        classname="icon icon-cogs",
        permissions=[
            "django_celery_beat.delete_periodic_task",
            "django_celery_beat.add_periodic_task",
            "django_celery_beat.change_periodic_task",
            "django_celery_beat.view_periodic_task",
        ],
        order=-12,
    )
)

# register permissions for wagtail admin:
@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtail_celery_beat',
        codename__in=[
            'run_periodic_task',
            'toggle_periodic_task',
            'enable_periodic_task',
            'disable_periodic_task',
        ]
    )
