# storyhub/urls.py
from django.contrib import admin
from django.urls import path, include
from stories.views_pages import CatalogView, StoryDetailView
from translations.views_pages import TranslatorDashboardView, EditorView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # HTML pages (SSR)
    path("", include("stories.urls_pages")),
    path("", include("translations.urls_pages")),
    path("", include("users.urls_pages")),

    # Аутентификация
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout/reset...
    path("accounts/", include("users.urls")),                # signup

    # API
    path("api/", include("stories.api_urls")),
    path("api/", include("translations.api_urls")),

    # DRF browseable API auth (опционально)
    path("api-auth/", include("rest_framework.urls")),
]