"""Host canonicalization middleware.

Why this exists (added 2026-08-10)
----------------------------------
Google Search Console reported three separate "not indexed" buckets that all
traced back to one fact: **www was a live 200 page, not a redirect.**

    http://acceleratedrehabtherapy.com/      -> 301 -> https://acceleratedrehabtherapy.com/
    http://www.acceleratedrehabtherapy.com/  -> 301 -> https://www.acceleratedrehabtherapy.com/

The www branch redirected to *itself* over HTTPS and then served the whole site.
`www.acceleratedrehabtherapy.com` is in ALLOWED_HOSTS, there is no PREPEND_WWW,
and nothing else canonicalized the host — so the only thing keeping www from
competing with the real domain was the <link rel="canonical"> tag added in
`context_processors.py`.

A canonical tag is a hint. A 301 is a directive. Google usually honors the hint,
but "usually" is what produced buckets #1, #3 and #4 in the first place.

nginx on the production host is the right place to terminate this, and it is
configured there. This middleware is the belt to that pair of braces: nginx
config lives outside this repo and outside the deploy pipeline, so nothing in
CI can assert it. This can be tested (see
`tests.py::CanonicalHostMiddlewareTests`), which means it cannot silently
regress the way the www/non-www split already did once.

Deliberately narrow
-------------------
It redirects exactly one host: `www.` + the CANONICAL_ORIGIN host. It does NOT
redirect anything else that isn't the canonical host, because ALLOWED_HOSTS also
carries `localhost`, `127.0.0.1`, `0.0.0.0` and the bare server IP — those are
dev and health-check paths, and blanket-redirecting them would break local work
and make the deploy's post-restart check bounce to production.
"""

from django.http import HttpResponsePermanentRedirect

from .context_processors import _canonical_origin


class CanonicalHostMiddleware:
    """301 the www host to CANONICAL_ORIGIN, preserving path and query.

    Runs before WhiteNoise so a www request never reaches static file serving
    or the view layer -- it costs one redirect and nothing else.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = _canonical_origin()
        # request.get_host() includes the port; the canonical host never does.
        host = request.get_host().split(':')[0].lower()

        if host == f'www.{origin.split("://", 1)[1]}':
            # get_full_path() keeps the query string. Unlike a canonical tag --
            # which deliberately strips query strings -- a redirect must not
            # drop them, or ?fbclid=... ad traffic landing on www would lose its
            # attribution parameters on the way to the real page.
            return HttpResponsePermanentRedirect(f'{origin}{request.get_full_path()}')

        return self.get_response(request)
