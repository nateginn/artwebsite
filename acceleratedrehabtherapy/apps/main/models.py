# acceleratedrehabtherapy/apps/main/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone


class MainPageConfig(models.Model):
    title = models.CharField(
        _('Title'), 
        max_length=128, 
        help_text=_('Page title')
    )
    description = models.TextField(
        _('Description'), 
        blank=True
    )
    text = CKEditor5Field(
        _('Content')
    )
    background = models.ImageField(
        _('Background'), 
        upload_to='main/background',
        blank=True,
        help_text=_('Main slider background - recommended size: 1400x800 pixels')
    )
    background_mobile = models.ImageField(
        _('Mobile Background'), 
        upload_to='main/background',
        blank=True,
        help_text=_('Mobile version - recommended size: 800x600 pixels')
    )
    background_tablet = models.ImageField(
        _('Tablet Background'), 
        upload_to='main/background',
        blank=True,
        help_text=_('Tablet version - recommended size: 1024x768 pixels')
    )
    slider_tagline = models.CharField(
        _('Slider Tagline'),
        max_length=128,
        default='keep your life moving',
        help_text=_('Text that appears in the slider')
    )
    button_text = models.CharField(
        _('Button Text'),
        max_length=64,
        default='I want to feel better',
        help_text=_('Call to action button text')
    )
    created = models.DateTimeField(
        _('Created'), 
        default=timezone.now
    )
    updated = models.DateTimeField(
        _('Updated'), 
        auto_now=True
    )

    class Meta:
        verbose_name = _('Page Content')
        verbose_name_plural = _('Page Contents')
        ordering = ['-created']

    def __str__(self):
        return self.title


class LandingPageLead(models.Model):
    SOURCE_CHOICES = [
        ('shockwave-denver', 'Shockwave Therapy Denver'),
        ('shockwave-greeley', 'Shockwave Therapy Greeley'),
        ('shockwave-plantar-fasciitis', 'Shockwave Plantar Fasciitis'),
        ('chronic-tendon', 'Chronic Tendon Pain'),
        ('non-surgical-denver', 'Non-Surgical Pain Relief Denver'),
    ]
    LOCATION_CHOICES = [
        ('greeley', 'Greeley'),
        ('denver', 'Denver'),
        ('no-preference', 'No Preference'),
    ]

    name = models.CharField(_('Name'), max_length=128)
    phone = models.CharField(_('Phone'), max_length=20)
    email = models.EmailField(_('Email'))
    condition = models.CharField(_('Condition / Reason for Visit'), max_length=256, blank=True)
    preferred_location = models.CharField(
        _('Preferred Location'), max_length=20, choices=LOCATION_CHOICES
    )
    source_page = models.CharField(_('Source Page'), max_length=50, choices=SOURCE_CHOICES)
    created = models.DateTimeField(_('Submitted'), default=timezone.now)

    class Meta:
        verbose_name = _('Landing Page Lead')
        verbose_name_plural = _('Landing Page Leads')
        ordering = ['-created']

    def __str__(self):
        return f"{self.name} — {self.get_source_page_display()} ({self.created.strftime('%Y-%m-%d')})"
