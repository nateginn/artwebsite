"""Deploy-time system checks for the main app.

These run on `manage.py check`, which the deploy workflow exercises via
`migrate`/`collectstatic`, so a misconfiguration fails the deploy loudly
instead of silently mis-serving the site.
"""

from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

from .context_processors import DEFAULT_CANONICAL_ORIGIN, validate_canonical_origin


@register()
def check_canonical_origin(app_configs, **kwargs):
    """CANONICAL_ORIGIN decides what the whole site advertises to Google.

    It is env-overridable, so a stale or malformed value in the server's .env
    would silently point every canonical tag and every sitemap entry at the
    wrong origin -- the failure mode that kept /massage/ out of the index once
    already. Validate it here rather than discovering it in Search Console.
    """
    raw = getattr(settings, 'CANONICAL_ORIGIN', DEFAULT_CANONICAL_ORIGIN)

    try:
        origin = validate_canonical_origin(raw)
    except ImproperlyConfigured as exc:
        return [Error(str(exc), id='main.E001', hint='Check CANONICAL_ORIGIN in the environment/.env.')]

    issues = []

    # In production the origin must be the real public site. A leftover
    # localhost/staging value here would deindex the site.
    #
    # This is an Error, not a Warning, deliberately: .github/workflows/deploy.yml
    # does not pass --fail-level WARNING, so a warning would print and the deploy
    # would proceed anyway -- shipping a whole site whose canonical tags and
    # sitemap point somewhere else. Errors abort management commands, so migrate
    # and collectstatic fail the deploy loudly instead.
    if not settings.DEBUG:
        if origin != DEFAULT_CANONICAL_ORIGIN:
            issues.append(Error(
                f"CANONICAL_ORIGIN is {origin!r}, not the expected production "
                f"origin {DEFAULT_CANONICAL_ORIGIN!r}. Every canonical tag and "
                "every sitemap entry would advertise this origin, which would "
                "deindex the real site.",
                id='main.E003',
                hint="Unset CANONICAL_ORIGIN in the server's .env to use the "
                     "production default. If the site genuinely moved domains, "
                     "update DEFAULT_CANONICAL_ORIGIN in "
                     "apps/main/context_processors.py -- a domain change should "
                     "be a reviewed code change, not an env var.",
            ))
        if origin.startswith('http://'):
            issues.append(Error(
                f"CANONICAL_ORIGIN uses http:// in production ({origin!r}); "
                "canonical URLs must be https://.",
                id='main.E002',
            ))

    return issues
