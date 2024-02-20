from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from wagtail.admin.panels import ObjectList, TabbedInterface, FieldPanel, HelpPanel, FieldRowPanel, MultiFieldPanel
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail.snippets.models import register_snippet
from wagtail.admin.menu import MenuItem, Menu
from wagtail import hooks

from celery import current_app
from kombu.utils.json import loads

from django_celery_beat.utils import is_database_scheduler
from django_celery_beat.admin import PeriodicTaskForm, TaskChoiceField
from django_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
    PeriodicTask,
)

from collections import namedtuple

MENU_HOOK_NAME = getattr(settings, "WCB_MENU_HOOK_NAME", "register_settings_menu_item")

class MetaSpoofer:
    def __init__(self, verbose_name, verbose_name_plural, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta = namedtuple("_meta", ["verbose_name", "verbose_name_plural"])(verbose_name, verbose_name_plural)
        self.wagtail_reference_index_ignore = True

#celery_menu = Menu(
#    register_hook_name="register_celery_menu",
#    construct_hook_name="construct_celery_menu",
#)

# Register your models here.
class ClockedScheduleAdmin(SnippetViewSet):
    """Admin-interface for clocked schedules."""

    fields = (
        'clocked_time',
    )
    list_display = (
        'clocked_time',
    )
    model = ClockedSchedule
    icon = "date"
    menu_label = "Clocked Schedules"


class CrontabScheduleAdmin(SnippetViewSet):
    list_display = ('__str__', 'human_readable')
    model = CrontabSchedule
    add_to_settings_menu = False
    exclude_from_explorer = False
    icon = "calendar-alt"

class IntervalScheduleAdmin(SnippetViewSet):
    model = IntervalSchedule
    add_to_settings_menu = False
    exclude_from_explorer = False
    icon = "history"
    menu_label = "Interval Schedules"

    panels = [
        FieldRowPanel([
            FieldPanel('every'),
            FieldPanel('period'),
        ], heading='Interval'),
    ]

class SolarScheduleAdmin(SnippetViewSet):
    model = SolarSchedule
    add_to_settings_menu = False
    exclude_from_explorer = False
    icon = "site"
    menu_label = "Solar Event Schedules"

from wagtail.admin.forms import WagtailAdminPageForm

class PeriodicTaskForm(WagtailAdminPageForm):
    """Form that lets you create and modify periodic tasks."""

    regtask = TaskChoiceField(
        label=_('Task (registered)'),
        required=False,
    )
    task = forms.CharField(
        label=_('Task (custom)'),
        required=False,
        max_length=200,
    )

    def clean(self):
        data = super().clean()
        regtask = data.get('regtask')
        if regtask:
            data['task'] = regtask
        if not data['task']:
            exc = forms.ValidationError(_('Need name of task'))
            self._errors['task'] = self.error_class(exc.messages)
            raise exc

        if data.get('expire_seconds') is not None and data.get('expires'):
            raise forms.ValidationError(
                _('Only one can be set, in expires and expire_seconds')
            )
        return data

    def _clean_json(self, field):
        value = self.cleaned_data[field]
        try:
            loads(value)
        except ValueError as exc:
            raise forms.ValidationError(
                _('Unable to parse JSON: %s') % exc,
            )
        return value

    def clean_args(self):
        return self._clean_json('args')

    def clean_kwargs(self):
        return self._clean_json('kwargs')
    
wrong_scheduler = not is_database_scheduler(getattr(settings, 'CELERY_BEAT_SCHEDULER', None))
extra_panels = []
if wrong_scheduler:
    extra_panels.append(HelpPanel(template="wagtail_celery_beat/partials/help_scheduler.html"))

# from wagtail.snippets.models import register_snippet
# IntervalSchedule = register_snippet(IntervalSchedule)
# CrontabSchedule = register_snippet(CrontabSchedule)
# SolarSchedule = register_snippet(SolarSchedule)
# ClockedSchedule = register_snippet(ClockedSchedule)

PeriodicTask.base_form_class = PeriodicTaskForm
PeriodicTask.edit_handler = TabbedInterface([
    ObjectList([
        *extra_panels,
        FieldPanel('name'),
        FieldRowPanel([
            FieldPanel('regtask'),
            FieldPanel('task'),
        ], heading='Task'),
        FieldPanel('description'),
        FieldPanel('last_run_at', read_only=True),
    ], heading=_('Periodic Task')),
    ObjectList([
        *extra_panels,
        HelpPanel(template="wagtail_celery_beat/partials/help_schedules.html"),
        FieldPanel('start_time', help_text=_('Start date and time when the task should start running.')),
        MultiFieldPanel([
            FieldPanel('interval', help_text=_('Interval Schedule to run the task on.')),#, widget=AdminSnippetChooser(model=IntervalSchedule)),
            FieldPanel('crontab', help_text=_('Crontab Schedule to run the task on.')),#, widget=AdminSnippetChooser(model=CrontabSchedule)),
            FieldPanel('solar', help_text=_('Solar Event Schedule to run the task on, this will be executed each time the event occurs.')),#, widget=AdminSnippetChooser(model=SolarSchedule)),
        ], heading=_('Periodically Scheduled'), classname='collapsible collapsed'),
        FieldPanel('clocked', 
            help_text=_('Clocked Schedule to run the task on, this will be executed only once at the specified time.'), 
            heading=_('Scheduled for specific date/time'),
            classname='collapsible collapsed'#, widget=AdminSnippetChooser(model=ClockedSchedule)
        ),
    ], heading=_('Schedule')),
    ObjectList([
        *extra_panels,
        FieldPanel('args'),
        FieldPanel('kwargs'),
    ], heading=_('Arguments')),
    ObjectList([
        *extra_panels,
        FieldRowPanel([
            FieldPanel('enabled'),
            FieldPanel('one_off'),
        ], heading=_('Execution')),
        FieldRowPanel([
            FieldPanel('expires'),
            FieldPanel('expire_seconds'),
        ], heading=_('Expiration')),
        MultiFieldPanel([
            FieldPanel('queue'),
            FieldPanel('exchange'),
            FieldPanel('routing_key'),
            FieldPanel('priority'),
            FieldPanel('headers'),
        ], heading=_('Advanced Options'), classname='collapsible collapsed'),
    ], heading=_('Execution Options')),
])

class PeriodicTaskAdmin(SnippetViewSet):
    """Admin-interface for periodic tasks."""

    icon = "cogs"
    menu_label = "Periodic Tasks"
    menu_order = -11
    model = PeriodicTask
    celery_app = current_app
    date_hierarchy = 'start_time'
    list_display = ('name', 'enabled', 'scheduler', 'interval', 'start_time',
                    'last_run_at', 'one_off')
    list_filter = ['enabled', 'one_off', 'task', 'start_time', 'last_run_at']
    actions = ('enable_tasks', 'disable_tasks', 'toggle_tasks', 'run_tasks')
    search_fields = ('name', 'description', 'task')
    # index_view_class = IndexViewSet

    def get_queryset(self, request):
        qs = self.model.objects.all()
        return qs.select_related('interval', 'crontab', 'solar', 'clocked')
    
#IntervalSchedule
#CrontabSchedule
#SolarSchedule
#ClockedSchedule
#PeriodicTask
    
try:
    from django_celery_results.models import (
        TaskResult,
        GroupResult,
    )


    class TaskResultAdmin(SnippetViewSet):
        """Admin-interface for results of tasks."""

        icon = "doc-full"
        menu_label = _("Task Results")

        model = TaskResult
        date_hierarchy = 'date_done'
        list_display = ('task_id', 'periodic_task_name', 'task_name', 'date_done',
                        'status', 'worker')
        list_filter = ('status', 'date_done', 'periodic_task_name', 'task_name',
                       'worker')
        readonly_fields = ('date_created', 'date_done', 'result', 'meta')
        search_fields = ('task_name', 'task_id', 'status', 'task_args',
                         'task_kwargs')

        edit_handler = TabbedInterface([
            ObjectList([
                FieldPanel('task_id', read_only=True),
                FieldPanel('task_name', read_only=True),
                FieldPanel('periodic_task_name', read_only=True),
                FieldPanel('status', read_only=True),
                FieldPanel('worker', read_only=True),
                FieldPanel('content_type', read_only=True),
                FieldPanel('content_encoding', read_only=True),
            ], heading=_('Task')),
            ObjectList([
                FieldPanel('task_args', read_only=True),
                FieldPanel('task_kwargs', read_only=True),
            ], heading=_('Parameters')),
            ObjectList([
                FieldPanel('result', read_only=True),
                FieldPanel('date_created', read_only=True),
                FieldPanel('date_done', read_only=True),
                FieldPanel('traceback', read_only=True),
                FieldPanel('meta', read_only=True),
            ], heading=_('Result')),
        ])


    class GroupResultAdmin(SnippetViewSet):
        """Admin-interface for results  of grouped tasks."""

        icon = "link"
        menu_label = _("Group Results")

        model = GroupResult
        date_hierarchy = 'date_done'
        list_display = ('group_id', 'date_done')
        list_filter = ('date_done',)
        readonly_fields = ('date_created', 'date_done', 'result')
        search_fields = ('group_id',)

    class ResultAdminGroup(SnippetViewSetGroup):
        menu_label = "Results"
        icon = "folder"
        menu_order = 200

        # hack to get nested inside another modeladmingroup.
        model = MetaSpoofer("Result", "Results") # no really, i think this is fucking disgusting, the worst of them all.

        items = (
            TaskResultAdmin,
            GroupResultAdmin,
        )

        def __init__(self, *args, **kwargs): # hack to get nested inside another modeladmingroup.
            super().__init__()
            self.parent = kwargs.pop("parent", None)

        def get_menu_item(self, order=None): # order added as hack to get nested inside another modeladmingroup.
            return super().get_menu_item()

    register_snippet(TaskResult, TaskResultAdmin)
    register_snippet(GroupResult, GroupResultAdmin)

    for_celery_admin_group = [
        ResultAdminGroup,
    ]
except ImportError:
    for_celery_admin_group = [
        # Empty if not installed
    ]




# create hook to register menu items
def register_to_celery_menu(menu_item: MenuItem):
    if callable(menu_item):
        item = menu_item()
        if item in CeleryAdminGroup.other_items:
            return
        CeleryAdminGroup.other_items.append(menu_item())
    else:
        if menu_item in CeleryAdminGroup.other_items:
            return
        CeleryAdminGroup.other_items.append(menu_item)

class ScheduleAdminGroup(SnippetViewSetGroup):
    """Admin-interface for clocked schedules."""
    menu_icon = "hourglass-split"
    menu_label = "Schedules"
    menu_order = 100

    # hack to get nested inside another modeladmingroup.
    model = MetaSpoofer("Schedule", "Schedules") # no really, i think this is fucking disgusting, the worst of them all.

    items = (
        ClockedScheduleAdmin,
        CrontabScheduleAdmin,
        IntervalScheduleAdmin,
        SolarScheduleAdmin,
    )

    other_items = []
    add_to_admin_menu = True
    add_to_settings_menu = True

    def __init__(self, *args, **kwargs): # hack to get nested inside another modeladmingroup.
        super().__init__()
        self.parent = kwargs.pop("parent", None)

    def get_menu_item(self, order=None): # order added as hack to get nested inside another modeladmingroup.
        return super().get_menu_item()



class CeleryAdminGroup(SnippetViewSetGroup):
    menu_label = _("Celery")
    icon = "clipboard-list"
    menu_order = 100
    menu = Menu(
        register_hook_name="register_celery_menu",
        construct_hook_name="construct_celery_menu",
    )
    items = (
        PeriodicTaskAdmin,
        ScheduleAdminGroup,
        *for_celery_admin_group,
    )

    other_items = []

    add_to_admin_menu = True
    add_to_settings_menu = True

    def get_submenu_items(self):
        items = super().get_submenu_items()
        items.extend(self.other_items)
        return sorted(items, key=lambda item: item.order)      

register_snippet(PeriodicTask, PeriodicTaskAdmin)
register_snippet(ClockedSchedule, ClockedScheduleAdmin)
register_snippet(CrontabSchedule, CrontabScheduleAdmin)
register_snippet(IntervalSchedule, IntervalScheduleAdmin)
register_snippet(SolarSchedule, SolarScheduleAdmin)

@hooks.register(MENU_HOOK_NAME)
def register_settings_menu_item():
    return CeleryAdminGroup().get_menu_item()
