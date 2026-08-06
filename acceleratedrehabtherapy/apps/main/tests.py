"""Tests for the main app.

Scope note: this repo deploys to production on every push to main, with no
staging environment (see CLAUDE.md). These tests exist to make that safe for the
specific things most likely to break silently -- sitemap contents and canonical
URLs -- not as a general testing initiative.
"""

import re
from xml.etree import ElementTree

from django.test import TestCase
from django.urls import URLPattern, URLResolver, reverse
from django.urls import get_resolver

from .sitemaps import LASTMOD, NON_PUBLIC_ROUTES, PUBLIC_PAGES

SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
CANONICAL_ORIGIN = 'https://acceleratedrehabtherapy.com'


def _collect_main_route_names():
    """Every named route in the `main` app URLconf, as 'main:<name>' strings."""
    names = set()
    for pattern in get_resolver().url_patterns:
        if isinstance(pattern, URLResolver) and pattern.namespace == 'main':
            for sub in pattern.url_patterns:
                if isinstance(sub, URLPattern) and sub.name:
                    names.add(f'main:{sub.name}')
    return names


class SitemapClassificationTests(TestCase):
    """The guard that makes adding pages safe.

    Registration is opt-in (PUBLIC_PAGES). This test walks the real URLconf and
    fails if a route is in neither PUBLIC_PAGES nor NON_PUBLIC_ROUTES, so a new
    route can be neither silently published nor silently omitted -- it forces a
    conscious decision.
    """

    def test_every_route_is_classified(self):
        all_routes = _collect_main_route_names()
        classified = set(PUBLIC_PAGES) | set(NON_PUBLIC_ROUTES)
        unclassified = all_routes - classified
        self.assertEqual(
            unclassified,
            set(),
            "Route(s) in the 'main' URLconf are classified neither as public "
            "nor non-public. Add each to PUBLIC_PAGES (to publish it in "
            "sitemap.xml) or to NON_PUBLIC_ROUTES with a reason (to exclude "
            f"it): {sorted(unclassified)}",
        )

    def test_no_stale_classifications(self):
        """Classifications must refer to routes that actually exist."""
        all_routes = _collect_main_route_names()
        stale = (set(PUBLIC_PAGES) | set(NON_PUBLIC_ROUTES)) - all_routes
        self.assertEqual(
            stale, set(),
            f"Classified route(s) no longer exist in the URLconf: {sorted(stale)}",
        )

    def test_public_and_non_public_are_disjoint(self):
        overlap = set(PUBLIC_PAGES) & set(NON_PUBLIC_ROUTES)
        self.assertEqual(overlap, set(), f"Route(s) both public and non-public: {sorted(overlap)}")

    def test_public_pages_has_no_duplicates(self):
        self.assertEqual(
            len(PUBLIC_PAGES), len(set(PUBLIC_PAGES)),
            "PUBLIC_PAGES contains duplicate entries, which would emit duplicate <url> blocks.",
        )

    def test_lastmod_entries_are_public_pages(self):
        orphans = set(LASTMOD) - set(PUBLIC_PAGES)
        self.assertEqual(orphans, set(), f"LASTMOD entries for non-public pages: {sorted(orphans)}")


class SitemapRenderTests(TestCase):
    """Assert the rendered XML, not just the Python config."""

    def setUp(self):
        self.response = self.client.get('/sitemap.xml')
        self.assertEqual(self.response.status_code, 200)
        self.root = ElementTree.fromstring(self.response.content)
        self.locs = [el.text for el in self.root.findall('.//sm:url/sm:loc', SITEMAP_NS)]

    def test_sitemap_is_wellformed_xml_with_expected_url_count(self):
        # setUp already parsed it; wellformedness is the assertion.
        self.assertEqual(len(self.locs), len(PUBLIC_PAGES))

    def test_exact_url_set(self):
        """Pins the exact set of published URLs.

        Any route added, removed, or renamed fails this until a human updates
        the expectation -- that is the point.
        """
        expected = {f'{CANONICAL_ORIGIN}{reverse(name)}' for name in PUBLIC_PAGES}
        self.assertEqual(set(self.locs), expected)

    def test_no_duplicate_locs(self):
        self.assertEqual(len(self.locs), len(set(self.locs)), "Duplicate <loc> entries in sitemap.")

    def test_every_loc_uses_canonical_origin(self):
        for loc in self.locs:
            self.assertTrue(
                loc.startswith(CANONICAL_ORIGIN + '/'),
                f"<loc> does not use the canonical non-www origin: {loc}",
            )

    def test_no_non_public_route_appears(self):
        for name in NON_PUBLIC_ROUTES:
            url = f'{CANONICAL_ORIGIN}{reverse(name)}'
            self.assertNotIn(
                url, self.locs,
                f"Non-public route {name} ({NON_PUBLIC_ROUTES[name]}) appeared in the sitemap.",
            )

    def test_ad_landing_pages_are_absent(self):
        """Explicit regression guard for the paid-campaign pages specifically."""
        body = self.response.content.decode()
        for slug in (
            'shockwave-therapy-denver',
            'shockwave-therapy-greeley',
            'shockwave-therapy-plantar-fasciitis',
            'chronic-tendon-pain-treatment',
            'non-surgical-pain-relief-denver',
            'thank-you',
        ):
            self.assertNotIn(
                f'{CANONICAL_ORIGIN}/{slug}/', body,
                f"Ad/utility page /{slug}/ must not be in the sitemap.",
            )

    def test_lastmod_is_never_the_render_date(self):
        """Guards the specific bug this replaced: {% now %} as lastmod.

        Every page claiming today's date on every crawl is what made the signal
        unreliable. Only pages with a real recorded date emit <lastmod>.
        """
        lastmods = [el.text for el in self.root.findall('.//sm:url/sm:lastmod', SITEMAP_NS)]
        self.assertEqual(
            len(lastmods), len(LASTMOD),
            "Number of <lastmod> elements should equal the number of recorded dates.",
        )
        for value in lastmods:
            self.assertRegex(value, r'^\d{4}-\d{2}-\d{2}$')
            self.assertIn(value, set(LASTMOD.values()))


class PublicPageSmokeTests(TestCase):
    """Every page we publish must actually render."""

    def test_all_public_pages_return_200(self):
        for name in PUBLIC_PAGES:
            with self.subTest(route=name):
                response = self.client.get(reverse(name))
                self.assertEqual(
                    response.status_code, 200,
                    f"{name} is published in the sitemap but did not return 200.",
                )

    def test_all_public_pages_emit_valid_json_ld(self):
        """Malformed JSON-LD fails silently in a browser; catch it here."""
        import json
        pattern = re.compile(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        for name in PUBLIC_PAGES:
            with self.subTest(route=name):
                body = self.client.get(reverse(name)).content.decode()
                for i, block in enumerate(pattern.findall(body)):
                    try:
                        json.loads(block)
                    except json.JSONDecodeError as exc:
                        self.fail(f"{name}: JSON-LD block #{i} is not valid JSON: {exc}")

    def test_no_placeholder_sameas_urls_remain(self):
        """Regression guard for the boilerplate sameAs that shipped site-wide."""
        body = self.client.get(reverse('main:home')).content.decode()
        self.assertNotIn('facebook.com/yourpage', body)
        self.assertNotIn('instagram.com/yourprofile', body)


class RemovedEndpointTests(TestCase):
    def test_debug_reviews_endpoint_is_gone(self):
        """It was public, unauthenticated, and leaked raw exception text."""
        self.assertEqual(self.client.get('/api/test-google-reviews/').status_code, 404)


class GoogleReviewsCacheTests(TestCase):
    """Negative caching for the Google Places call.

    An empty or failed upstream response used to be left uncached, so a Places
    outage produced a live upstream call on every request, from every worker.
    The subtle part is that an empty list is a *valid cached value*: a
    truthiness check (`if cached_reviews:`) silently treats every negative-cache
    entry as a miss, which reintroduces the bug while looking fixed.
    """

    def setUp(self):
        from django.core.cache import cache
        cache.delete('google_reviews')
        self.addCleanup(cache.delete, 'google_reviews')

    def test_empty_cached_result_is_a_hit_not_a_miss(self):
        from unittest import mock
        from django.core.cache import cache
        from . import views

        cache.set('google_reviews', [], 900)
        # If the empty entry were treated as a miss, this would attempt a live
        # HTTP call; patching requests.get lets us assert it never happens.
        with mock.patch.object(views.requests, 'get') as mock_get:
            result = views.get_google_reviews()
        self.assertEqual(result, [])
        mock_get.assert_not_called()

    def test_upstream_failure_is_negative_cached(self):
        from unittest import mock
        from django.core.cache import cache
        from . import views

        with mock.patch.dict(
            'os.environ',
            {'GOOGLE_MAPS_API_KEY': 'test-key', 'GOOGLE_PLACE_ID': 'test-place'},
        ):
            with mock.patch.object(
                views.requests, 'get', side_effect=Exception("upstream down")
            ) as mock_get:
                first = views.get_google_reviews()
                self.assertEqual(first, [])
                self.assertEqual(mock_get.call_count, 1)

                # Second call must be served from the negative cache.
                second = views.get_google_reviews()
                self.assertEqual(second, [])
                self.assertEqual(
                    mock_get.call_count, 1,
                    "Failed upstream response was not negative-cached; Google "
                    "would be re-hit on every request during an outage.",
                )

    def test_missing_credentials_are_not_cached(self):
        """Misconfiguration should recover immediately once env vars are set."""
        from unittest import mock
        from django.core.cache import cache
        from . import views

        with mock.patch.dict('os.environ', {}, clear=True):
            self.assertEqual(views.get_google_reviews(), [])
        self.assertIsNone(
            cache.get('google_reviews'),
            "Missing credentials must not be cached, or fixing the env var "
            "would not take effect until the TTL expired.",
        )
