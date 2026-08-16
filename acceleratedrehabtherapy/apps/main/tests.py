"""Tests for the main app.

Scope note: this repo deploys to production on every push to main, with no
staging environment (see CLAUDE.md). These tests exist to make that safe for the
specific things most likely to break silently -- sitemap contents and canonical
URLs -- not as a general testing initiative.
"""

import re
from xml.etree import ElementTree

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver, reverse
from django.urls import get_resolver

from django.conf import settings

from .sitemaps import LASTMOD, NON_PUBLIC_ROUTES, PUBLIC_PAGES

SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
CANONICAL_ORIGIN = settings.CANONICAL_ORIGIN.rstrip('/')

CANONICAL_RE = re.compile(
    r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.IGNORECASE
)
OG_URL_RE = re.compile(
    r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"', re.IGNORECASE
)


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


class CanonicalUrlTests(TestCase):
    """Canonical/OG URLs must be host-pinned and query-free.

    Two separate live defects motivated this:
      * request.build_absolute_uri() used the *request's* host, so a page served
        over www self-canonicalized to www while the sitemap advertised non-www.
      * It also kept the query string, so Meta Ads traffic arriving at
        /page/?fbclid=... canonicalized each tracking variant to itself.
    """

    LANDING_ROUTE = 'main:landing_shockwave_denver'

    def _canonical_of(self, response):
        match = CANONICAL_RE.search(response.content.decode())
        self.assertIsNotNone(match, "No <link rel=\"canonical\"> found on the page.")
        return match.group(1)

    def test_canonical_strips_fbclid_on_standard_pages(self):
        """The specific Meta Ads defect, on a base.html page."""
        url = reverse('main:massage')
        response = self.client.get(url, {'fbclid': 'IwAR_test_123'})
        self.assertEqual(
            self._canonical_of(response), f'{CANONICAL_ORIGIN}{url}',
            "Canonical must drop the query string, not canonicalize the "
            "tracking-parameter variant to itself.",
        )

    def test_canonical_strips_fbclid_on_ad_landing_pages(self):
        """base_landing.html is where fbclid traffic actually arrives."""
        url = reverse(self.LANDING_ROUTE)
        response = self.client.get(url, {'fbclid': 'IwAR_test_123', 'utm_source': 'fb'})
        self.assertEqual(self._canonical_of(response), f'{CANONICAL_ORIGIN}{url}')

    def test_canonical_ignores_request_host(self):
        """A non-canonical host must still canonicalize to the pinned origin.

        This used to send a www request. It can't any more -- CanonicalHostMiddleware
        now 301s www before a page is ever rendered, so there is no canonical tag
        in that response to inspect (see CanonicalHostMiddlewareTests).

        The bare server IP is the right vehicle now: it is in ALLOWED_HOSTS, it is
        deliberately NOT redirected (the deploy's post-restart check uses it), and
        it still renders. So it is exactly the case this test exists for -- a host
        that isn't the canonical one and whose pages must not mirror it.
        """
        url = reverse('main:massage')
        response = self.client.get(url, HTTP_HOST='146.190.174.50')
        self.assertEqual(self._canonical_of(response), f'{CANONICAL_ORIGIN}{url}')

    def test_og_url_matches_canonical(self):
        for route in ('main:massage', self.LANDING_ROUTE):
            with self.subTest(route=route):
                url = reverse(route)
                body = self.client.get(url, {'fbclid': 'x'}).content.decode()
                og = OG_URL_RE.search(body)
                self.assertIsNotNone(og, f"No og:url on {route}")
                self.assertEqual(og.group(1), f'{CANONICAL_ORIGIN}{url}')

    def test_every_public_page_self_canonicalizes_to_pinned_origin(self):
        for name in PUBLIC_PAGES:
            with self.subTest(route=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(self._canonical_of(response), f'{CANONICAL_ORIGIN}{url}')

    def test_no_template_uses_build_absolute_uri_for_urls(self):
        """Guard against reintroducing the pattern in a new template.

        `request.get_host` is checked as well as `build_absolute_uri`: both
        mirror whatever host the visitor arrived on, which is the defect this
        guards. Checking only the latter is why six templates kept building
        og:image and JSON-LD `image` URLs as
        `{{ request.scheme }}://{{ request.get_host }}...` long after the
        canonical fix -- and `request.scheme` also emitted http:// behind the
        proxy, which some social platforms refuse to load at all.
        """
        from pathlib import Path
        root = Path(settings.BASE_DIR) / 'acceleratedrehabtherapy'
        banned = ('build_absolute_uri', 'request.get_host')
        offenders = []
        for path in root.rglob('*.html'):
            if 'staticfiles' in path.parts:
                continue
            text = path.read_text(encoding='utf-8', errors='ignore')
            for pattern in banned:
                if pattern in text:
                    offenders.append(f'{path.relative_to(root)}: {pattern}')
        self.assertEqual(
            offenders, [],
            "Use {{ canonical_url }} or {{ canonical_origin }} instead of "
            f"request-derived hosts for canonical/OG/schema URLs: {offenders}",
        )

    def test_sitemap_origin_matches_page_canonical_origin(self):
        """The sitemap and the canonical tags must not drift apart."""
        sitemap_body = self.client.get('/sitemap.xml').content.decode()
        page_url = reverse('main:massage')
        canonical = self._canonical_of(self.client.get(page_url))
        self.assertIn(f'{CANONICAL_ORIGIN}{page_url}', sitemap_body)
        self.assertTrue(canonical.startswith(CANONICAL_ORIGIN + '/'))


class CanonicalOriginConfigTests(TestCase):
    """Guards the setting itself, not just consistency with it.

    CanonicalUrlTests derives its expectations from settings.CANONICAL_ORIGIN,
    so it proves pages and sitemap *agree* — it would pass just as happily if
    the setting were wrong. These tests pin the real value and reject malformed
    ones.
    """

    # Deliberately hardcoded, NOT read from settings. If someone changes the
    # setting, this test should fail and make them justify it.
    EXPECTED_PRODUCTION_ORIGIN = 'https://acceleratedrehabtherapy.com'

    def test_production_origin_is_the_real_site(self):
        from .context_processors import DEFAULT_CANONICAL_ORIGIN
        self.assertEqual(DEFAULT_CANONICAL_ORIGIN, self.EXPECTED_PRODUCTION_ORIGIN)
        self.assertEqual(
            settings.CANONICAL_ORIGIN.rstrip('/'), self.EXPECTED_PRODUCTION_ORIGIN,
            "CANONICAL_ORIGIN is not the production origin. Every canonical tag "
            "and sitemap entry advertises this value.",
        )

    def test_valid_origins_are_normalized(self):
        from .context_processors import validate_canonical_origin
        self.assertEqual(
            validate_canonical_origin('https://example.com/'), 'https://example.com'
        )
        self.assertEqual(
            validate_canonical_origin('  https://example.com  '), 'https://example.com'
        )

    def test_malformed_origins_are_rejected(self):
        from django.core.exceptions import ImproperlyConfigured
        from .context_processors import validate_canonical_origin

        bad_values = [
            '',                                   # empty
            '   ',                                # whitespace only
            'acceleratedrehabtherapy.com',        # no scheme
            'ftp://acceleratedrehabtherapy.com',  # wrong scheme
            'https://',                           # no host
            'https://example.com/some/path',      # has a path
            'https://example.com?a=b',            # has a query
            'https://example.com#frag',           # has a fragment
            'https://exa mple.com',               # space
            'https://example.com" onload="x',     # attribute-breaking
            None,                                 # wrong type
        ]
        for value in bad_values:
            with self.subTest(value=value):
                with self.assertRaises(ImproperlyConfigured):
                    validate_canonical_origin(value)

    def test_system_check_passes_with_current_settings(self):
        from .checks import check_canonical_origin
        self.assertEqual(check_canonical_origin(None), [])

    def test_system_check_errors_on_malformed_value(self):
        from .checks import check_canonical_origin
        with self.settings(CANONICAL_ORIGIN='not-a-url'):
            issues = check_canonical_origin(None)
        self.assertTrue(issues)
        self.assertEqual(issues[0].id, 'main.E001')

    def test_system_check_errors_on_non_production_origin_when_not_debug(self):
        """Must be an ERROR, not a warning.

        deploy.yml does not pass --fail-level WARNING, so a warning would print
        and the deploy would continue -- publishing a site whose canonical tags
        and sitemap all point at the wrong origin. Errors abort management
        commands, so migrate/collectstatic fail the deploy instead.
        """
        from django.core.checks import Error as CheckError
        from .checks import check_canonical_origin
        with self.settings(DEBUG=False, CANONICAL_ORIGIN='https://staging.example.com'):
            issues = check_canonical_origin(None)
        ids = {i.id for i in issues}
        self.assertIn('main.E003', ids)
        for issue in issues:
            if issue.id == 'main.E003':
                self.assertIsInstance(issue, CheckError)
                self.assertTrue(issue.is_serious())

    def test_system_check_errors_on_http_in_production(self):
        from .checks import check_canonical_origin
        with self.settings(DEBUG=False, CANONICAL_ORIGIN='http://acceleratedrehabtherapy.com'):
            ids = {i.id for i in check_canonical_origin(None)}
        self.assertIn('main.E002', ids)

    def test_es_info_canonical_is_html_escaped(self):
        """/es/ bypasses the template engine, so escaping is manual."""
        response = self.client.get(reverse('main:es_info'))
        body = response.content.decode()
        self.assertIn(
            f'<link rel="canonical" href="{CANONICAL_ORIGIN}/es/">', body
        )
        self.assertNotIn('__CANONICAL_URL__', body)


class PhoneNumberTests(TestCase):
    """No page may advertise a phone number that doesn't ring.

    +19703517465 sat in the JSON-LD `telephone` field of four service pages
    (chiropractor, massage, physical_therapy, acupuncture) while every visible
    tel: link on the site used the correct Greeley number. It was a dead line.

    That is the worst possible place to hide one: structured data is what Google
    reads for rich results and the knowledge panel, so the number a searcher taps
    can come from JSON-LD without ever appearing in the page text a human would
    proofread. Nothing about the rendered page looked wrong.
    """

    # Every number the site is allowed to publish, digits only.
    APPROVED = {
        '+19703241750',   # Greeley -- 1823 65th Ave
        '+17206042792',   # Denver -- 2480 W 26th Ave
        '+19703512412',   # UNC Campus -- Cassidy Hall
    }
    RETIRED = '9703517465'

    TELEPHONE_RE = re.compile(r'"telephone"\s*:\s*"([^"]+)"')

    def _templates(self):
        from pathlib import Path
        root = Path(settings.BASE_DIR) / 'acceleratedrehabtherapy'
        for path in root.rglob('*.html'):
            if 'staticfiles' in path.parts or 'node_modules' in path.parts:
                continue
            yield path, path.read_text(encoding='utf-8', errors='ignore')

    def test_retired_number_appears_nowhere(self):
        offenders = [
            str(path) for path, text in self._templates()
            if self.RETIRED in text.replace('-', '').replace('.', '')
        ]
        self.assertEqual(
            offenders, [],
            f"The retired number {self.RETIRED} is a dead line and must not be "
            f"published: {offenders}",
        )

    def test_structured_data_phone_numbers_are_approved(self):
        """Covers JSON-LD on every published page, rendered rather than scanned."""
        for name in PUBLIC_PAGES:
            with self.subTest(route=name):
                body = self.client.get(reverse(name)).content.decode()
                for raw in self.TELEPHONE_RE.findall(body):
                    normalized = re.sub(r'[^\d+]', '', raw)
                    self.assertIn(
                        normalized, self.APPROVED,
                        f"{name} publishes an unapproved telephone value {raw!r}. "
                        "Add it to PhoneNumberTests.APPROVED only if it really rings.",
                    )


class CanonicalHostMiddlewareTests(TestCase):
    """www must 301 to the canonical host, not serve a second copy of the site.

    Before this middleware, www.acceleratedrehabtherapy.com answered every URL
    with a live 200 and relied solely on <link rel="canonical"> to stop Google
    treating it as a separate site. Google reported it in three separate "not
    indexed" buckets. nginx now also terminates this, but nginx config lives
    outside this repo and outside CI -- these tests are the only thing that can
    fail a build if the behavior disappears again.
    """

    WWW_HOST = f'www.{CANONICAL_ORIGIN.split("://", 1)[1]}'

    def test_www_root_redirects_permanently_to_canonical_origin(self):
        response = self.client.get('/', HTTP_HOST=self.WWW_HOST)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], f'{CANONICAL_ORIGIN}/')

    def test_www_preserves_path(self):
        url = reverse('main:massage')
        response = self.client.get(url, HTTP_HOST=self.WWW_HOST)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], f'{CANONICAL_ORIGIN}{url}')

    def test_www_preserves_query_string(self):
        """Unlike the canonical tag, the redirect must NOT strip the query.

        This clinic runs Meta Ads. A www click carrying ?fbclid=... that landed
        on a query-stripped redirect would lose its attribution parameters.
        """
        response = self.client.get(
            '/shockwave-therapy-denver/',
            {'fbclid': 'ABC123'},
            HTTP_HOST=self.WWW_HOST,
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response['Location'],
            f'{CANONICAL_ORIGIN}/shockwave-therapy-denver/?fbclid=ABC123',
        )

    def test_www_redirects_before_the_url_resolver(self):
        """Even a nonexistent path must redirect rather than 404 on www.

        Proves the middleware short-circuits ahead of WhiteNoise and routing --
        a 404 here would mean www still gets to answer requests itself.
        """
        response = self.client.get('/no-such-page/', HTTP_HOST=self.WWW_HOST)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], f'{CANONICAL_ORIGIN}/no-such-page/')

    def test_canonical_host_is_not_redirected(self):
        host = CANONICAL_ORIGIN.split('://', 1)[1]
        response = self.client.get('/', HTTP_HOST=host)
        self.assertEqual(response.status_code, 200)

    def test_local_and_healthcheck_hosts_are_not_redirected(self):
        """ALLOWED_HOSTS also carries dev hosts and the bare server IP.

        Blanket-redirecting every non-canonical host would break local
        development and bounce the deploy's post-restart check to production.
        """
        for host in ('localhost', '127.0.0.1', 'testserver'):
            with self.subTest(host=host):
                response = self.client.get('/', HTTP_HOST=host)
                self.assertEqual(response.status_code, 200)


class UnpublishedTeamPageTests(TestCase):
    """The team scaffold must stay invisible until real bios are added.

    It exists so that publishing is a content task rather than a build task,
    but a placeholder page leaking into search results would be worse than no
    page at all. These tests are what make it safe to leave in the tree.
    """

    def test_page_renders(self):
        self.assertEqual(self.client.get(reverse('main:team')).status_code, 200)

    def test_page_is_noindex(self):
        body = self.client.get(reverse('main:team')).content.decode()
        self.assertIn('name="robots" content="noindex, nofollow"', body)
        self.assertNotIn('name="robots" content="index, follow"', body)

    def test_page_is_not_in_sitemap(self):
        body = self.client.get('/sitemap.xml').content.decode()
        self.assertNotIn(reverse('main:team'), body)

    def test_page_is_not_linked_from_nav(self):
        """Nav renders on every page; a link there would expose the draft."""
        home = self.client.get(reverse('main:home')).content.decode()
        self.assertNotIn(f'href="{reverse("main:team")}"', home)

    def test_indexable_pages_still_say_index_follow(self):
        """The new {% block robots %} must not have broken the default."""
        body = self.client.get(reverse('main:home')).content.decode()
        self.assertIn('name="robots" content="index, follow"', body)

    def test_contains_no_real_looking_credentials(self):
        """Guard against someone half-filling the placeholders and forgetting.

        If real bios get added, this test should be deleted along with the
        robots block -- it is a tripwire for the draft state, not a rule.
        """
        body = self.client.get(reverse('main:team')).content.decode()
        self.assertIn('[ PROVIDER NAME ]', body)
        self.assertIn('Draft page', body)


class ShockwavePageTests(TestCase):
    """Guards the focused-shockwave positioning on /shockwave-therapy/.

    Both clinics run focused (fESWT) devices while competitors typically run
    radial, and the page said nothing about it -- the differentiator was
    invisible. These tests pin the claim to the places that actually carry it
    (title, H1, meta description, the focused-vs-radial explainer) so a future
    copy edit cannot quietly drop it back to generic "shockwave therapy".
    """

    META_DESCRIPTION_RE = re.compile(
        r'<meta name="description" content="([^"]*)"', re.IGNORECASE
    )

    # Coverage that predates the focused rewrite and must survive it.
    CONDITIONS = [
        'Plantar fasciitis',
        'Achilles tendon pain',
        'Tennis elbow',
        'Shoulder pain',
        'Chronic tendon injuries',
        'Scar tissue restrictions',
    ]

    def setUp(self):
        self.body = self.client.get(reverse('main:shockwave')).content.decode()

    def test_title_and_h1_claim_focused(self):
        self.assertIn(
            '<title>Focused Shockwave Therapy in Greeley & Denver | '
            'Accelerated Rehab Therapy</title>',
            self.body,
        )
        self.assertIn('Focused Shockwave Therapy in Greeley & Denver, CO', self.body)

    def test_meta_description_is_present_and_fits_the_serp(self):
        match = self.META_DESCRIPTION_RE.search(self.body)
        self.assertIsNotNone(match, 'No <meta name="description"> on the page.')
        description = match.group(1)
        self.assertIn('Focused shockwave therapy', description)
        self.assertLess(
            len(description), 150,
            f'Meta description is {len(description)} chars; Google truncates it.',
        )

    def test_clinical_terminology_is_present(self):
        """The searched-for terms, in descending order of prominence."""
        for term in (
            'focused shockwave therapy',
            'Extracorporeal shockwave therapy (ESWT)',
            'fESWT',
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.body)

    def test_focused_versus_radial_is_explained(self):
        self.assertIn('Focused vs. Radial Shockwave', self.body)
        self.assertIn('Radial shockwave', self.body)
        self.assertIn(
            'Both our Greeley and Denver clinics use focused shockwave devices',
            self.body,
        )

    def test_condition_coverage_survived_the_rewrite(self):
        for condition in self.CONDITIONS:
            with self.subTest(condition=condition):
                self.assertIn(condition, self.body)

    def test_focused_is_not_also_used_as_a_massage_analogy(self):
        """On this page "focused" means the device type, not an intensity."""
        self.assertNotIn('focused deep tissue massage', self.body)

    def test_eswt_synonym_faq_is_present(self):
        """ESWT is its own search term; the FAQ is its rich-result surface."""
        self.assertIn(
            '<h3 class="text-lg font-bold mb-2" itemprop="name">'
            'Is shockwave therapy the same as ESWT?</h3>',
            self.body,
        )
        self.assertIn('ESWT stands for extracorporeal shockwave therapy', self.body)

    def test_every_faq_question_is_marked_up_for_rich_results(self):
        """A Question without itemprop="mainEntity" is invisible to rich results.

        This include is the site's reference implementation of FAQPage markup --
        elsewhere the wrapper exists but the questions lack mainEntity, so only
        one of them publishes. Adding a question here without the itemprop would
        silently repeat that bug.
        """
        questions = self.body.count('itemtype="https://schema.org/Question"')
        answers = self.body.count('itemtype="https://schema.org/Answer"')
        entities = self.body.count('itemprop="mainEntity"')
        self.assertEqual(questions, 6, f'Expected 6 FAQs, found {questions}.')
        self.assertEqual(
            entities, questions,
            f'{questions - entities} question(s) lack itemprop="mainEntity".',
        )
        self.assertEqual(answers, questions, 'Every question needs an answer.')

    def test_no_outcome_or_cure_promises(self):
        """Claims stay mechanistic: no cures, guarantees, or success rates."""
        for pattern in (
            r'\bcures?\b',
            r'\bguarantee(d|s)?\b',
            r'\bsuccess rate\b',
            r'\b\d+% of patients\b',
        ):
            with self.subTest(pattern=pattern):
                self.assertIsNone(
                    re.search(pattern, self.body, re.IGNORECASE),
                    f'Page contains an outcome promise matching {pattern}.',
                )


class ResourcesBlogTests(TestCase):
    """Guards the /resources/ blog content.

    Articles live as #anchors on this one page rather than at their own URLs.
    The category cards link to those anchors, so a renamed or deleted article id
    breaks a visible link with nothing else to catch it.
    """

    NEW_ARTICLE_IDS = [
        'blog-delayed-symptoms',
        'blog-colorado-work-injury',
        'blog-back-pain-evidence',
        'blog-first-visit-safety',
        'blog-desk-setup-movement',
    ]

    # Read and cleared by the clinician named in the byline.
    CLINICALLY_REVIEWED_IDS = [
        'blog-delayed-symptoms',
        'blog-back-pain-evidence',
        'blog-first-visit-safety',
        'blog-desk-setup-movement',
    ]

    REVIEWER = 'Nathan Ginn, DC, L.Ac., FIAMA'

    def setUp(self):
        self.body = self.client.get(reverse('main:resources')).content.decode()

    def test_all_new_articles_present(self):
        for article_id in self.NEW_ARTICLE_IDS:
            with self.subTest(article=article_id):
                self.assertIn(f'<article id="{article_id}"', self.body)

    def test_no_broken_internal_anchors(self):
        """Every #blog-* link on the page must resolve to an article on it."""
        ids = set(re.findall(r'<article id="([^"]+)"', self.body))
        hrefs = set(re.findall(r'href="#(blog-[^"]+)"', self.body))
        self.assertEqual(
            hrefs - ids, set(),
            f"Category card(s) link to article anchors that do not exist: {sorted(hrefs - ids)}",
        )

    def test_no_dead_placeholder_links_remain(self):
        """The category cards previously all pointed at href="#"."""
        self.assertNotIn('<a href="#" class="inline-block mt-4', self.body)

    def test_each_new_article_cites_sources(self):
        """Sourcing is the point of these articles; an uncited one is a defect."""
        for article_id in self.NEW_ARTICLE_IDS:
            with self.subTest(article=article_id):
                start = self.body.index(f'<article id="{article_id}"')
                end = self.body.index('</article>', start)
                section = self.body[start:end]
                self.assertIn('<h5>Sources</h5>', section)
                self.assertIn('href="https://', section)

    def _article_html(self, article_id):
        start = self.body.index(f'<article id="{article_id}"')
        return self.body[start:self.body.index('</article>', start)]

    def test_clinical_articles_name_their_reviewer(self):
        """A review claim must name who made it, not assert review generically."""
        for article_id in self.CLINICALLY_REVIEWED_IDS:
            with self.subTest(article=article_id):
                section = self._article_html(article_id)
                self.assertIn('medically reviewed by:', section.lower())
                self.assertIn(self.REVIEWER, section)
                self.assertIn('Last reviewed:', section)

    def test_legal_article_names_no_reviewer(self):
        """The work-injury article is published on its disclaimer, not on review.

        Clinical sign-off does not validate a statutory deadline, so this one
        deliberately carries no reviewer while the other four do. Asserting the
        absence stops a later edit from extending the clinical byline across the
        whole page for consistency's sake -- which would attribute a legal
        review to a clinician. A named reviewer here needs to be someone
        competent in Colorado workers' compensation.
        """
        section = self._article_html('blog-colorado-work-injury')
        self.assertNotIn('reviewed by:', section.lower())
        self.assertIn('Last updated:', section)

    def test_no_review_placeholders_remain(self):
        """Unfilled placeholders must never survive to a published page.

        These articles shipped with "[ PENDING CLINICAL REVIEW ]" bylines and
        yellow draft banners while awaiting sign-off. Publishing meant removing
        both by hand, which is exactly the kind of edit that misses one.
        """
        for marker in ('PENDING', '[ DATE ]', 'pending review'):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.body)

    def test_no_unverified_citation_urls(self):
        """Tripwire for fabricated citations.

        A URL invented by pattern-matching a plausible-looking path is the
        exact failure mode this content must not have: during authoring, two
        guessed source URLs turned out to be wrong (one NINDS path that does
        not exist, one MedlinePlus article that is about a different
        condition entirely). This pins the citations that were verified to
        resolve and to be on-topic, so a future edit cannot quietly swap in
        an unchecked one.
        """
        verified = {
            'https://www.ncbi.nlm.nih.gov/books/NBK537200/',
            'https://www.acpjournals.org/doi/10.7326/M16-2367',
            'https://pubmed.ncbi.nlm.nih.gov/28192793/',
            'https://www.nccih.nih.gov/health/spinal-manipulation-what-you-need-to-know',
            'https://pubmed.ncbi.nlm.nih.gov/20227325/',
            'https://pmc.ncbi.nlm.nih.gov/articles/PMC5719861/',
            'https://pubmed.ncbi.nlm.nih.gov/17916783/',
            'https://pmc.ncbi.nlm.nih.gov/articles/PMC2446396/',
            'https://pubmed.ncbi.nlm.nih.gov/8164827/',
            'https://www.cdc.gov/stroke/signs-symptoms/index.html',
            'https://www.cdc.gov/traumatic-brain-injury/signs-symptoms/index.html',
            'https://www.cdc.gov/physical-activity-basics/guidelines/adults.html',
            'https://www.cdc.gov/niosh/ergonomics/index.html',
            'https://www.osha.gov/etools/computer-workstations/positions',
            'https://www.osha.gov/etools/computer-workstations/components/monitors',
            'https://cdle.colorado.gov/dwc/injured-workers/reporting-your-injury',
            'https://cdle.colorado.gov/dwc/employers/reporting-injuries',
            'https://leg.colorado.gov/bills/hb22-1112',
        }
        cited = set()
        for article_id in self.NEW_ARTICLE_IDS:
            section = self._article_html(article_id)
            sources_at = section.find('<h5>Sources</h5>')
            if sources_at != -1:
                cited.update(re.findall(r'href="(https://[^"]+)"', section[sources_at:]))
        unverified = cited - verified
        self.assertEqual(
            unverified, set(),
            "Citation URL(s) not in the verified set. Fetch each one and confirm "
            "it resolves AND covers the claim before adding it here: "
            f"{sorted(unverified)}",
        )

    def test_legal_article_requires_more_than_clinical_review(self):
        """Clinical sign-off does not validate a legal deadline."""
        section = self._article_html('blog-colorado-work-injury')
        self.assertIn('not legal advice', section.lower())
        self.assertIn('workers\' compensation attorney', section.lower())

    def test_page_does_not_claim_all_content_is_reviewed(self):
        """Blanket review claims must not outrun actual review status.

        Removed 2026-08-06 and confirmed by the owner on review that it stays
        removed. It is still false: the older articles on this page carry no
        reviewer, and the work-injury article is published on its disclaimer
        rather than a named reviewer. A page-level claim would cover both.
        """
        self.assertNotIn(
            'All resources are reviewed by our medical professionals', self.body,
            "Page-level review claim covers articles that have no named "
            "reviewer. Review claims belong in individual bylines.",
        )

    def test_emergency_guidance_present_on_clinical_articles(self):
        """Red-flag guidance is the safety-critical part of this content."""
        expectations = {
            'blog-delayed-symptoms': ['911', 'emergency'],
            'blog-back-pain-evidence': ['emergency department', 'cauda equina'],
            'blog-first-visit-safety': ['911', 'stroke'],
        }
        for article_id, needles in expectations.items():
            start = self.body.index(f'<article id="{article_id}"')
            end = self.body.index('</article>', start)
            section = self.body[start:end].lower()
            for needle in needles:
                with self.subTest(article=article_id, needle=needle):
                    self.assertIn(needle.lower(), section)

    # The articles published on /resources/, as of LASTMOD['main:resources'].
    #
    # Adding, removing, or renaming a post changes this set and fails the test
    # below. Fixing that failure means editing this list *and* bumping
    # LASTMOD['main:resources'] to the day the change was made -- which is the
    # point. The page's "Last updated" line renders from that same LASTMOD
    # entry, so the visible date cannot drift away from the actual content.
    #
    # Honest limit: this forces the date to be *reconsidered* whenever the
    # article set changes. It cannot verify the date you type is truthful, and
    # it deliberately ignores body-copy edits -- otherwise every typo fix would
    # fail CI.
    PUBLISHED_ARTICLES = (
        'blog-auto-injury',
        'blog-back-pain-evidence',
        'blog-better-posture',
        'blog-colorado-work-injury',
        'blog-delayed-symptoms',
        'blog-desk-setup-movement',
        'blog-first-visit-safety',
        'blog-neck-pain',
        'blog-unlocking-wellness',
    )

    def test_article_set_matches_the_recorded_last_updated_date(self):
        """Adding a post must force the 'Last updated' date to be revisited."""
        from .sitemaps import LASTMOD

        on_page = tuple(sorted(re.findall(r'<article id="(blog-[^"]+)"', self.body)))
        self.assertEqual(
            on_page, tuple(sorted(self.PUBLISHED_ARTICLES)),
            "The set of articles on /resources/ changed.\n"
            "Update PUBLISHED_ARTICLES above AND bump "
            f"LASTMOD['main:resources'] (currently {LASTMOD.get('main:resources')!r}) "
            "in sitemaps.py to the date of the change. The disclaimer's "
            "'Last updated' line and the sitemap both read from that entry.",
        )

    def test_last_updated_is_a_real_date_not_the_render_date(self):
        """The disclaimer date must be a fixed fact, not today's date."""
        from datetime import date
        from .sitemaps import last_updated

        stamp = last_updated('main:resources')
        self.assertIsNotNone(
            stamp, "/resources/ needs a LASTMOD entry to display a date at all"
        )
        self.assertLessEqual(stamp, date.today(), "lastmod is in the future")
        self.assertNotIn(
            '{% now', self.body, "Template still renders a self-advancing date"
        )
        self.assertIn(
            stamp.strftime('Last updated: %B ') + str(stamp.day), self.body,
            "The rendered disclaimer date does not match LASTMOD['main:resources']",
        )

    def test_article_images_sit_below_their_heading(self):
        """Every article leads with its <h3>, then the image, then the body.

        Two of the older posts had the image above the heading and two below,
        which read as unfinished on a page where the posts sit side by side in
        a grid. Heading-first also keeps the element that names the section
        ahead of the decorative content in the DOM.
        """
        article_re = re.compile(
            r'<article id="(blog-[^"]+)"[^>]*>(.*?)</article>', re.DOTALL
        )
        offenders = []
        for match in article_re.finditer(self.body):
            slug, inner = match.group(1), match.group(2)
            heading = re.search(r'<h3\b', inner)
            image = re.search(r'<(?:picture|img)\b', inner)
            if heading is None:
                offenders.append(f'{slug}: no <h3> at all')
            elif image is not None and image.start() < heading.start():
                offenders.append(f'{slug}: image appears above the <h3>')

        self.assertEqual(
            offenders, [],
            "Blog post images must sit below their heading:\n  "
            + "\n  ".join(offenders),
        )

    def test_external_source_links_are_safe(self):
        """target="_blank" without rel=noopener is a known tab-nabbing vector."""
        for match in re.finditer(r'<a\b[^>]*target="_blank"[^>]*>', self.body):
            tag = match.group(0)
            self.assertIn('rel="noopener noreferrer"', tag, f"Unsafe external link: {tag}")


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


class StaticAssetReferenceTests(TestCase):
    """Every `{% static %}` path in a template must resolve to a real file.

    This exists because four <picture> blocks on /resources/ referenced .webp
    files that were never created (cb96fc4, 2025-11-05). The images were broken
    in production for nine months and nothing caught it, because a missing
    static file is not an error anywhere -- the page still returns 200.

    The failure is specific to <picture>: the browser picks the first <source>
    whose `type` it supports, and if that URL 404s it does *not* fall back to
    the next <source> or to the <img>. So a missing .webp shows nothing at all,
    even with a perfectly good .png sitting right beneath it.
    """

    STATIC_TAG_RE = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]\s*%\}""")

    # Assets that are referenced but do not exist. Each is a real defect, not a
    # false positive. The test fails on anything NOT in this set, so the debt is
    # pinned and cannot quietly grow.
    #
    # These four are the `image` property of the MedicalBusiness JSON-LD on the
    # service pages, so the structured data currently points Google at a 404.
    # They need real photographs of the clinic delivering each service --
    # substituting the logo or a stock image would misrepresent the practice, so
    # they stay listed until somebody supplies actual photos.
    #
    # The favicon set, site.webmanifest and og-default.jpg used to be here too.
    # They were generated from the clinic's own logo on 2026-08-06; before that,
    # apple-touch-icon.png was the only declared icon that resolved and it was a
    # stock globe, which is what Google showed beside the business name.
    KNOWN_MISSING = frozenset({
        'img/acupuncture.jpg',
        'img/chiropractic-care.jpg',
        'img/massage-therapy.jpg',
        'img/physical-therapy.jpg',
    })

    def _template_files(self):
        from pathlib import Path

        roots = []
        for engine in settings.TEMPLATES:
            roots.extend(Path(d) for d in engine.get('DIRS', []))
        roots.append(Path(settings.BASE_DIR) / 'apps' / 'main' / 'templates')

        seen = set()
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob('*.html'):
                if path not in seen:
                    seen.add(path)
                    yield path

    def test_every_static_reference_resolves(self):
        from django.contrib.staticfiles import finders

        missing = []
        checked = 0
        for template in self._template_files():
            text = template.read_text(encoding='utf-8', errors='replace')
            for asset in self.STATIC_TAG_RE.findall(text):
                checked += 1
                if asset in self.KNOWN_MISSING:
                    continue
                if finders.find(asset) is None:
                    missing.append(f'{template.name}: {asset}')

        self.assertGreater(checked, 0, "Found no {% static %} references at all")
        self.assertEqual(
            missing, [],
            "Templates reference static files that do not exist:\n  "
            + "\n  ".join(sorted(set(missing))),
        )

    def test_known_missing_list_has_no_stale_entries(self):
        """If someone supplies a missing asset, make them delete its excuse.

        Without this, KNOWN_MISSING rots into a permanent allowlist and the
        sweep above silently stops covering assets that now exist.
        """
        from django.contrib.staticfiles import finders

        now_present = sorted(a for a in self.KNOWN_MISSING if finders.find(a) is not None)
        self.assertEqual(
            now_present, [],
            "These assets now exist and must be removed from KNOWN_MISSING so "
            "they are covered by the sweep again:\n  " + "\n  ".join(now_present),
        )

    def test_picture_sources_all_exist(self):
        """Narrower guard on the exact construct that broke.

        Kept separate from the sweep above so the failure message names the
        <picture> fallback trap rather than reading as a generic missing file.
        """
        from django.contrib.staticfiles import finders

        source_re = re.compile(r'<source[^>]+srcset="\{%\s*static\s+[\'"]([^\'"]+)[\'"]\s*%\}"')
        missing = []
        for template in self._template_files():
            text = template.read_text(encoding='utf-8', errors='replace')
            for asset in source_re.findall(text):
                if finders.find(asset) is None:
                    missing.append(f'{template.name}: {asset}')

        self.assertEqual(
            missing, [],
            "A <picture> <source> points at a missing file. Browsers will show "
            "NO image rather than falling back to the <img>:\n  "
            + "\n  ".join(sorted(set(missing))),
        )


class LandingPageFocusedShockwaveTests(TestCase):
    """Ad copy promising focused shockwave must land on a page that says so.

    `/shockwave-therapy/` was rewritten to lead with focused (fESWT) while the
    five noindex ad landing pages still said generic "shockwave therapy" -- a
    paid click on a focused-shockwave ad arrived at a page that did not
    corroborate the claim. These pages are noindex and carry no organic risk,
    so the guard is message-match, not SEO: every page that sells shockwave
    names the device type.
    """

    ROUTES = [
        'main:landing_shockwave_denver',
        'main:landing_shockwave_greeley',
        'main:landing_shockwave_plantar_fasciitis',
        'main:landing_chronic_tendon',
        'main:landing_non_surgical_denver',
    ]

    def _body(self, route):
        return self.client.get(reverse(route)).content.decode()

    def test_every_shockwave_landing_page_claims_focused(self):
        for route in self.ROUTES:
            with self.subTest(route=route):
                self.assertIn('ocused shockwave', self._body(route))

    def test_focused_is_not_also_used_as_a_massage_analogy(self):
        """"Focused" means the device type here, the same as on /shockwave-therapy/."""
        for route in self.ROUTES:
            with self.subTest(route=route):
                self.assertNotIn('focused deep tissue massage', self._body(route))

    def test_pages_stay_noindex(self):
        """The focused claim must not arrive with accidental indexability.

        These pages duplicate `/shockwave-therapy/`'s subject matter. Indexed,
        they would compete with the money page for the term it was just
        rewritten to own.
        """
        for route in self.ROUTES:
            with self.subTest(route=route):
                self.assertIn(
                    '<meta name="robots" content="noindex, nofollow">',
                    self._body(route),
                )


@override_settings(
    EMAIL_HOST_USER='leads@example.com',
    DEFAULT_FROM_EMAIL='noreply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ContactFormSubmissionTests(TestCase):
    """Every contact-form POST returned 500 until 2026-08-15.

    `urls.py` sets `app_name = 'main'`, so the route is only reachable as
    `main:contact`; the view redirected to the bare name `contact` and raised
    NoReverseMatch. `send_mail` had already run by then, so the lead was
    delivered and the visitor saw a server error instead of the confirmation.

    EMAIL_HOST_USER is `os.getenv('EMAIL_HOST_USER')` with no default
    (`settings.py:328`), so it is None in any environment without a populated
    .env -- these settings are overridden so the test asserts the view's
    behaviour rather than the runner's environment.
    """

    def test_valid_submission_redirects_to_contact_and_sends_mail(self):
        response = self.client.post(reverse('main:contact'), {
            'name': 'Test Person',
            'email': 'test@example.com',
            'message': 'Please call me about shockwave therapy.',
        })
        self.assertRedirects(response, reverse('main:contact'))
        self.assertEqual(len(mail.outbox), 1)

    def test_missing_required_field_redirects_without_sending(self):
        response = self.client.post(reverse('main:contact'), {'name': 'Test Person'})
        self.assertRedirects(response, reverse('main:contact'))
        self.assertEqual(len(mail.outbox), 0)
