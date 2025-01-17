# acceleratedrehabtherapy/apps/main/urls.py

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path("", views.home, name="home"),  # Root URL for the app
    path("chiropractor/", views.chiropractor, name="chiropractor"), # Chiropractor page
    path("auto-injury/", views.auto_injury, name="auto_injury"),  # Auto injury page
    path("work-comp/", views.work_comp, name="work_comp"), #work comp page
    path("contact/", views.contact, name="contact"),  # Contact page
    path("api/reviews/", views.reviews_api, name="reviews_api"),
    path("api/test-google-reviews/", views.test_google_reviews, name="test_google_reviews"),
]
