from django.urls import path
from . import views

app_name = "wagtail_celery_beat"

urlpatterns = [
    path("", views.IndexListView.as_view(), name="index"),
]