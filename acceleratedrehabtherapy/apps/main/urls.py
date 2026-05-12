# acceleratedrehabtherapy/apps/main/urls.py

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path("", views.home, name="home"),  # Root URL for the app
    path("chiropractor/", views.chiropractor, name="chiropractor"), # Chiropractor page
    path("massage/", views.massage, name="massage"),  # Massage page
    path("physical-therapy/", views.physical_therapy, name="physical_therapy"),  # Physical therapy page
    path("acupuncture/", views.acupuncture, name="acupuncture"),  # Acupuncture page
    path("auto-injury/", views.auto_injury, name="auto_injury"),  # Auto injury page
    path("work-comp/", views.work_comp, name="work_comp"), #work comp page
    path("contact/", views.contact, name="contact"),  # Contact page
    path("about/", views.about, name="about_us"),  # About page
    path("resources/", views.resources, name="resources"),  # Resources page  
    path("api/reviews/", views.reviews_api, name="reviews_api"),
    path("api/test-google-reviews/", views.test_google_reviews, name="test_google_reviews"),
    # Spanish info page (not linked in top menu)
    path("es/", views.es_info, name="es_info"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),  # Privacy policy page
    # Landing pages — Meta Ads campaigns (not linked in main nav)
    path("shockwave-therapy-denver/", views.landing_shockwave_denver, name="landing_shockwave_denver"),
    path("shockwave-therapy-greeley/", views.landing_shockwave_greeley, name="landing_shockwave_greeley"),
    path("shockwave-therapy-plantar-fasciitis/", views.landing_shockwave_plantar_fasciitis, name="landing_shockwave_plantar_fasciitis"),
    path("chronic-tendon-pain-treatment/", views.landing_chronic_tendon, name="landing_chronic_tendon"),
    path("non-surgical-pain-relief-denver/", views.landing_non_surgical_denver, name="landing_non_surgical_denver"),
    path("landing/submit/", views.landing_form_submit, name="landing_form_submit"),
    path("thank-you/", views.landing_thank_you, name="landing_thank_you"),
]
