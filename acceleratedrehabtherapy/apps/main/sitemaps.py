# acceleratedrehabtherapy/apps/main/sitemaps.py

"""Sitemap definitions for the main app.

Design note (2026-08-06)
------------------------
This file used to hold a hand-maintained list of 14 URL names. That is
fail-open in the direction that matters here: a new public page is simply
forgotten and never appears in sitemap.xml, which is invisible until someone
notices the page isn't indexed. The site's own history shows this class of
problem is real.

The fix is NOT "derive everything from the URLconf" -- that is fail-open in the
other direction, silently publishing internal routes the moment they're added.

So: registration is explicit and opt-in (PUBLIC_PAGES below), and a test
(`test_sitemap.py::test_every_route_is_classified`) walks the real URLconf and
fails if any route is in neither PUBLIC_PAGES nor NON_PUBLIC_ROUTES. Adding a
route therefore forces a conscious include/exclude decision, and the default for
an unclassified route is "not published".

`templates/sitemap.xml` renders `{% url url.item %}`, so `items()` must yield
URL *name* strings. Do not change the return shape without updating that
template -- it fails silently otherwise.
"""

from django.contrib.sitemaps import Sitemap


# Public, indexable pages. Adding a page here is what publishes it.
# `lastmod` is a real date per page -- see LASTMOD below.
PUBLIC_PAGES = [
    'main:home',
    'main:chiropractor',
    'main:massage',
    'main:physical_therapy',
    'main:acupuncture',
    'main:shockwave',
    'main:auto_injury',
    'main:work_comp',
    'main:contact',
    'main:about_us',
    'main:resources',
    'main:es_info',
    'main:privacy_policy',
    'main:eula',
]

# Routes that must NEVER appear in the sitemap, each with the reason.
# The exhaustiveness test reads this, so an entry here is a deliberate,
# reviewable decision rather than an omission.
NON_PUBLIC_ROUTES = {
    # Meta Ads campaign landing pages. Deliberately excluded from organic
    # discovery (see urls.py) -- they are paid-traffic destinations with
    # campaign-specific offers and should not compete in search.
    'main:landing_shockwave_denver': 'Meta Ads landing page',
    'main:landing_shockwave_greeley': 'Meta Ads landing page',
    'main:landing_shockwave_plantar_fasciitis': 'Meta Ads landing page',
    'main:landing_chronic_tendon': 'Meta Ads landing page',
    'main:landing_non_surgical_denver': 'Meta Ads landing page',
    # Post-conversion page; no standalone search value.
    'main:landing_thank_you': 'post-submit confirmation page',
    # Form handler, not a page.
    'main:landing_form_submit': 'POST handler, not a page',
    # JSON endpoints, not pages.
    'main:reviews_api': 'JSON API endpoint',
    # Unpublished scaffold: renders noindex placeholder content with no real
    # provider names or credentials. Move to PUBLIC_PAGES only after the
    # publish checklist at the top of main/team.html is completed.
    'main:team': 'unpublished scaffold (noindex, placeholder content)',
}

# Real per-page last-modified dates (YYYY-MM-DD).
#
# The previous template emitted `{% now 'Y-m-d' %}` for every URL, so every page
# claimed it had changed *today*, on every single crawl. Google discounts
# lastmod it judges unreliable, which devalued the signal site-wide.
#
# A page with no entry here simply omits <lastmod>, which is correct and
# honest -- an absent lastmod is strictly better than a false one.
LASTMOD = {
    'main:shockwave': '2026-08-03',      # page added
    'main:eula': '2026-07-30',           # page added
    'main:about_us': '2026-08-06',       # UNC seasonal copy corrected
    'main:privacy_policy': '2025-05-24',
}


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        # Must yield URL-name strings: templates/sitemap.xml does {% url url.item %}.
        return list(PUBLIC_PAGES)

    def location(self, item):
        # Not used by the custom template (which reverses `url.item` itself),
        # but Django's Sitemap API calls it, and keeping it correct means the
        # framework default template would also work.
        from django.urls import reverse
        return reverse(item)

    def lastmod(self, item):
        from datetime import date
        stamp = LASTMOD.get(item)
        if not stamp:
            return None
        return date.fromisoformat(stamp)

    def priority(self, item):
        if item == 'main:home':
            return 1.0
        return 0.8
