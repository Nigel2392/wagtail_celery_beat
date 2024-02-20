from typing import Any
from django.urls import reverse
from django.views.generic import ListView
from django_celery_beat.models import PeriodicTask
from django.http import HttpResponseRedirect
from collections import OrderedDict
from wagtail.admin import messages
from django.utils.translation import gettext_lazy as _
from .actions import WAGTAIL_CELERY_BEAT_ACTIONS
from .admin import PeriodicTaskAdmin
from django.contrib.auth.mixins import PermissionRequiredMixin


# Create your views here.
class IndexListView(PermissionRequiredMixin, ListView):
    model = PeriodicTask
    template_name = "wagtail_celery_beat/celery_admin/index.html"
    context_object_name = "tasks"
    actions = WAGTAIL_CELERY_BEAT_ACTIONS
    permission_required = [
        "django_celery_beat.delete_periodic_task",
        "django_celery_beat.add_periodic_task",
        "django_celery_beat.change_periodic_task",
        "django_celery_beat.view_periodic_task"
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        actions = self.actions() if callable(self.actions) else self.actions
        actions = sorted(actions, key=lambda a: a.order)
        self.action_dict = OrderedDict()
        for action in actions:
            self.action_dict[action.id()] = action
        self.task_admin_page = PeriodicTaskAdmin()

    def get_actions(self):
        return self.action_dict.values()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = [action for action in self.get_actions() if action.is_shown(self.request)]
        context["edit_task_url"] = self.task_admin_page.get_url_name("edit")
        context["add_task_url"] = self.task_admin_page.get_url_name("add")
        return context

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get("periodic_task_action")
        if action:
            if action not in self.action_dict:
                messages.error(self.request, "Invalid action")
                return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
            
            action = self.action_dict[action]
            if not action.is_shown(self.request):
                messages.error(self.request, "You do not have permission to perform this action")
                return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
            
            selected = self.request.POST.getlist("selected_for_task")
            if not selected:
                messages.error(self.request, "No tasks selected")
                return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))

            queryset = self.get_queryset().filter(pk__in=selected)

        #try:
            return action.handle(self.request, queryset)
        #except Exception as e:
        #    messages.error(self.request, f"Exception occurred while executing action: {e}")
        #    return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
            
        messages.error(self.request, "No action selected")
        return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
            