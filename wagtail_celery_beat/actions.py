from django.urls import reverse
from django_celery_beat.models import PeriodicTasks
from django.db.models import Case, When, Value
from django.http import HttpResponseRedirect
from wagtail.admin import messages
from celery import current_app
from kombu.utils.json import loads
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import pluralize
from .action import Action

WAGTAIL_CELERY_BEAT_ACTIONS = lambda _: [
        Action(
            label="Run",
            handler=run_tasks,
            icon="crosshairs",
            permissions=[
                "wagtail_celery_beat.run_periodic_task",
            ]
        ),
        Action(
            label="Toggle",
            handler=toggle_tasks,
            icon="resubmit",
            permissions=[
                "wagtail_celery_beat.toggle_periodic_task",
                "wagtail_celery_beat.enable_periodic_task",
                "wagtail_celery_beat.disable_periodic_task",
            ]
        ),
        Action(
            label="Enable",
            handler=enable_tasks,
            icon="circle-check",
            permissions=[
                "wagtail_celery_beat.enable_periodic_task",
                "wagtail_celery_beat.toggle_periodic_task",
            ]
        ),
        Action(
            label="Disable",
            handler=disable_tasks,
            icon="error",
            permissions=[
                "wagtail_celery_beat.disable_periodic_task",
                "wagtail_celery_beat.toggle_periodic_task",
            ]
        ),
        #Action(
        #    label="Delete",
        #    handler=delete_tasks,
        #),
    ]

#def delete_tasks(request, queryset):
#    length = queryset.count()
#    queryset.delete()
#    messages.success(request, f'{length} {_("tasks deleted successfully")}')
#    return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
    
def run_tasks(request, queryset):
    app = current_app
    app.loader.import_default_modules()


    
    tasks = [(app.tasks.get(task.task),
              loads(task.args),
              loads(task.kwargs),
              task.queue,
              task.name)
             for task in queryset]

    if any(t[0] is None for t in tasks):
        for i, t in enumerate(tasks):
            if t[0] is None:
                break

        # variable "i" will be set because list "tasks" is not empty
        not_found_task_name = queryset[i].task

        messages.error(request, f'task "{not_found_task_name}" not found')
    else:
        task_ids = [
            task.apply_async(args=args, kwargs=kwargs, queue=queue,
                             periodic_task_name=periodic_task_name)
            if queue and len(queue)
            else task.apply_async(args=args, kwargs=kwargs,
                                  periodic_task_name=periodic_task_name)
            for task, args, kwargs, queue, periodic_task_name in tasks
        ]
        tasks_run = len(task_ids)
        if tasks_run < 1:
            messages.error(request, _("No tasks were run, does the task still exist?"))
        else:
            messages.success(request, _("{0} task{1} {2} successfully run".format(
                tasks_run,
                pluralize(tasks_run),
                pluralize(tasks_run, _('was,were')),
            )))
    return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))

def _message_user_about_update(request, rows_updated, verb):
    """Send message about action to user.
    `verb` should shortly describe what have changed (e.g. 'enabled').
    """
    if rows_updated < 1:
        messages.error(request, _("No tasks were {0}, does the task still exist?".format(verb)))
        return
    messages.success(
        request,
        _('{0} task{1} {2} successfully {3}').format(
            rows_updated,
            pluralize(rows_updated),
            pluralize(rows_updated, _('was,were')),
            verb,
        ),
    )

def enable_tasks(request, queryset):
    rows_updated = queryset.update(enabled=True)
    PeriodicTasks.update_changed()
    _message_user_about_update(request, rows_updated, 'enabled')

def disable_tasks(request, queryset):
    rows_updated = queryset.update(enabled=False, last_run_at=None)
    PeriodicTasks.update_changed()
    _message_user_about_update(request, rows_updated, 'disabled')

def _toggle_tasks_activity(queryset):
    return queryset.update(enabled=Case(
        When(enabled=True, then=Value(False)),
        default=Value(True),
    ))

def toggle_tasks(request, queryset):
    rows_updated = _toggle_tasks_activity(queryset)
    PeriodicTasks.update_changed()
    _message_user_about_update(request, rows_updated, 'toggled')
