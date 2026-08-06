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
        """A www request must still canonicalize to the pinned origin."""
        url = reverse('main:massage')
        response = self.client.get(url, HTTP_HOST='www.acceleratedrehabtherapy.com')
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
        """Guard against reintroducing the pattern in a new template."""
        from pathlib import Path
        root = Path(settings.BASE_DIR) / 'acceleratedrehabtherapy'
        offenders = []
        for path in root.rglob('*.html'):
            if 'staticfiles' in path.parts:
                continue
            if 'build_absolute_uri' in path.read_text(encoding='utf-8', errors='ignore'):
                offenders.append(str(path.relative_to(root)))
        self.assertEqual(
            offenders, [],
            "Use {{ canonical_url }} instead of request.build_absolute_uri for "
            f"canonical/OG/schema URLs: {offenders}",
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

    # Assets that are referenced but have never existed in the repo. Each one is
    # a real defect, not a false positive -- all nine 404 in production today.
    # They are listed here rather than fixed because each needs a design asset
    # somebody has to actually produce, and shipping a wrong-looking favicon or
    # OG card is worse than shipping none. The test fails on anything NOT in
    # this set, so the debt is pinned and cannot quietly grow.
    #
    #   og-default.jpg  -- og:image AND twitter:image on every page (base.html).
    #                      Every social share of this site has no preview card.
    #   img/<service>.jpg -- the `image` property of MedicalBusiness JSON-LD on
    #                      the four service pages, so the structured data points
    #                      at a 404.
    #   favicon.* / site.webmanifest -- no favicon anywhere on the site.
    KNOWN_MISSING = frozenset({
        'img/og-default.jpg',
        'img/favicon.ico',
        'img/favicon-32x32.png',
        'img/favicon-16x16.png',
        'site.webmanifest',
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
