"""Template context processors for the main app.

Canonical URL handling (added 2026-08-06)
-----------------------------------------
Templates previously built canonical/OG/schema URLs from
`{{ request.build_absolute_uri }}`, which has two defects:

1. It uses the *request's* host. The sitemap pins the canonical non-www
   domain, so a page served over www self-canonicalized to www while the
   sitemap advertised non-www — the exact www/non-www split that this site's
   own sitemap.xml comment blames for /massage/ falling out of Google's index.

2. It includes the *query string*. This clinic runs Meta Ads, so real traffic
   arrives at URLs like /shockwave-therapy-denver/?fbclid=ABC123 — and each of
   those was telling Google "this tracking-parameter URL is the canonical
   version of itself", splitting ranking signal across unlimited variants of
   the pages they pay to drive traffic to.

`canonical_url` fixes both: fixed origin, path only, no query.
"""

from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_CANONICAL_ORIGIN = 'https://acceleratedrehabtherapy.com'


def validate_canonical_origin(value):
    """Return a normalized origin, or raise ImproperlyConfigured.

    This value is env-overridable, and it decides what every page and the
    sitemap advertise to Google. A stale, empty, or malformed value would
    silently mis-canonicalize the entire site, so it is validated rather than
    trusted. It is also interpolated into HTML, so anything that isn't a bare
    scheme+host is rejected outright.
    """
    if not isinstance(value, str) or not value.strip():
        raise ImproperlyConfigured("CANONICAL_ORIGIN must be a non-empty string.")

    origin = value.strip().rstrip('/')
    parts = urlsplit(origin)

    if parts.scheme not in ('http', 'https'):
        raise ImproperlyConfigured(
            f"CANONICAL_ORIGIN must start with http:// or https:// (got {value!r})."
        )
    if not parts.netloc:
        raise ImproperlyConfigured(f"CANONICAL_ORIGIN has no host (got {value!r}).")
    if parts.path or parts.query or parts.fragment:
        raise ImproperlyConfigured(
            "CANONICAL_ORIGIN must be scheme+host only, with no path, query, or "
            f"fragment (got {value!r})."
        )
    # Defense in depth: this string is interpolated into href attributes.
    if any(c in origin for c in '"\'<> '):
        raise ImproperlyConfigured(
            f"CANONICAL_ORIGIN contains characters unsafe for HTML (got {value!r})."
        )
    return origin


def _canonical_origin():
    """Scheme+host that every canonical URL is built from.

    Overridable via the CANONICAL_ORIGIN setting so a staging/preview host
    doesn't advertise production URLs, but it is deliberately a single value
    rather than request-derived — that's the whole point.
    """
    return validate_canonical_origin(
        getattr(settings, 'CANONICAL_ORIGIN', DEFAULT_CANONICAL_ORIGIN)
    )


def build_canonical_url(request):
    """Absolute canonical URL for this request: fixed origin + path, no query."""
    return f"{_canonical_origin()}{request.path}"


def canonical(request):
    return {
        'canonical_url': build_canonical_url(request),
        'canonical_origin': _canonical_origin(),
    }
