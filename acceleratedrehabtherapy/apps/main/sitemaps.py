# acceleratedrehabtherapy/apps/main/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # Return a list of URL names for your static pages
        return [
            'main:home',
            'main:chiropractor',
            'main:massage',
            'main:physical_therapy',
            'main:acupuncture',
            'main:auto_injury',
            'main:work_comp',
            'main:contact',
            'main:about_us',
            'main:resources',
            'main:es_info',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        # Give the home page a higher priority
        if item == 'main:home':
            return 1.0
        return 0.8
