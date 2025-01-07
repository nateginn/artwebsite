# acceleratedrehabtherapy/apps/main/urls.py

from django.urls import path
from . import views

app_name = 'main'  # Add this line to set the namespace

urlpatterns = [
    path("", views.MainPageView.as_view(), name="home"),  # Root URL for the app
]
