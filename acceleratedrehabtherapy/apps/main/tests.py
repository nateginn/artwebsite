import json
import re

from django.test import TestCase
from django.urls import reverse


class ShockwavePageTests(TestCase):
    """Smoke test for the /shockwave-therapy/ service page.

    Scoped narrowly to this one route rather than a general suite,
    because production deploys on every push to main with no staging
    environment (see CLAUDE.md) — a broken template or malformed JSON-LD
    here would ship straight to a live medical clinic's site.
    """

    def setUp(self):
        self.url = reverse('main:shockwave')
        self.response = self.client.get(self.url)

    def test_renders_with_correct_template(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, 'main/shockwave.html')

    def test_listed_in_sitemap(self):
        sitemap_response = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap_response.status_code, 200)
        self.assertContains(sitemap_response, self.url)

    def test_nav_label_appears_in_both_dropdown_variants(self):
        # "Shockwave Therapy" legitimately appears more than twice on this
        # page (title/OG/schema name/H1 all use the service name too), so
        # match the specific dropdown menu-item markup rather than the
        # bare phrase, to isolate "both nav variants render" from
        # "the page mentions its own name".
        content = self.response.content.decode()
        menu_item_count = content.count('role="menuitem">Shockwave Therapy</a>')
        self.assertEqual(menu_item_count, 2)

    def test_json_ld_blocks_are_valid_and_provider_free(self):
        content = self.response.content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        self.assertTrue(blocks, "expected at least one JSON-LD block")

        therapy_blocks = []
        for raw in blocks:
            data = json.loads(raw)  # raises loudly on malformed JSON
            if data.get('@type') == 'MedicalTherapy':
                therapy_blocks.append(data)

        self.assertEqual(len(therapy_blocks), 1)
        self.assertNotIn('provider', therapy_blocks[0])

    def test_faq_microdata_is_complete(self):
        content = self.response.content.decode()
        question_count = content.count('itemtype="https://schema.org/Question"')
        answer_count = content.count('itemtype="https://schema.org/Answer"')
        self.assertEqual(question_count, 5)
        self.assertEqual(answer_count, 5)

    def test_hero_image_reference(self):
        self.assertContains(self.response, 'IMG_4078_web.jpg')
