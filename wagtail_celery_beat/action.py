from django.utils.text import slugify
from wagtail.admin import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

class Action(object):
    def __init__(self, label, handler, icon="cog", order=0, success_url="wagtail_celery_beat:index", success_message=None, permissions=None):
        """
            Handler will be a function which takes a queryset.
            If it returns an HTTPResponse, it will be returned to the user,
            otherwise the user will be redirected back and a message will be displayed.
            This will be a response to a POST request.

            fn(request, queryset) -> HTTPResponse | None
        """
        self.label = label
        self.handler = handler
        self.icon = icon
        self.order = order
        self.success_url = success_url
        self.success_message = success_message
        self.permissions = permissions
        

    def id(self):
        return f"action-{slugify(self.label + str(self.hash()))}"
    
    def hash(self):
        return hash(self)
    
    def __hash__(self):
        return hash(self.label + str(self.order) + str(self.icon))
    
    def is_shown(self, request):
        if self.permissions and not request.user.has_perms(self.permissions):
            return False
        return True

    def handle(self, request, queryset):
        if self.permissions:
            if not request.user.has_perms(self.permissions):
                messages.error(request, "You do not have permission to perform this action")
                return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))
        resp = self.handler(request, queryset)
        if resp is not None and isinstance(resp, HttpResponse):
            return resp
        if self.success_message:
            messages.success(request, self.success_message() if callable(self.success_message) else self.success_message)
        if self.success_url:
            return HttpResponseRedirect(reverse(self.success_url))
        return HttpResponseRedirect(reverse("wagtail_celery_beat:index"))

    def __str__(self):
        return self.label

    def __repr__(self):
        return self.__str__()
