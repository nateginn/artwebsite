from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acceleratedrehabtherapy.apps.main"

    def ready(self):
        # Registers the CANONICAL_ORIGIN system check so a bad value fails
        # `manage.py check` at deploy time rather than silently mis-serving
        # every canonical tag and sitemap entry.
        from . import checks  # noqa: F401
