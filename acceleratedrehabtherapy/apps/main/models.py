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
