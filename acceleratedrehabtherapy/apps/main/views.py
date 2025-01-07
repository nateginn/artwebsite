# acceleratedrehabtherapy/apps/main/views.py
from dataclasses import dataclass
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.template.response import TemplateResponse

from .models import MainPageConfig


@dataclass
class MainPageContext:
    """Structured data class for main page context"""
    config: MainPageConfig
    is_main_page: bool = True
    meta_title: str | None = None
    meta_description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'config': self.config,
            'is_main_page': self.is_main_page,
            'meta_title': self.meta_title or self.config.title,
            'meta_description': self.meta_description or self.config.description
        }


class MainPageView(ListView):
    model = MainPageConfig
    template_name = 'main/home.html'
    context_object_name = 'pages'
    ordering = ['-created']

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @method_decorator(require_GET)
    def dispatch(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.object_list:
            latest = self.object_list[0]
            context['page'] = latest
            context['meta_title'] = latest.title
            context['meta_description'] = latest.description
        return context

    def render_to_response(self, context: dict[str, Any], **response_kwargs: Any) -> TemplateResponse:
        """Override to add custom headers or response modifications if needed"""
        response = super().render_to_response(context, **response_kwargs)
        return response
