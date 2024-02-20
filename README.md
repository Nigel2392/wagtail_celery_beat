wagtail_celery_beat
===================

`pip install wagtail_celery_beat`

Manage your celery tasks from the Wagtail admin with Wagtail Celery Beat, a wrapper for Django Celery Beat.

When `django_celery_results` is installed the task results viewset will be included in the Wagtail Celery Beat menu by default.

Quick start
-----------

1. Add 'wagtail_celery_beat' to your INSTALLED_APPS setting like this:

   ```
   INSTALLED_APPS = [
   ...,
   'wagtail_celery_beat',
   ]
   ```
2. Run `py ./manage.py collectstatic`
3. Enjoy!


### Optional setting:

`WCB_MENU_HOOK_NAME` Registers to a `wagtail.admin.menu` using this hook name.

By default registers to settings menu.
