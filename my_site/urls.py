from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from blog.sitemaps import PostSitemap
from markdownx import urls as markdownx_urls

from .metrics import metrics_view
from .site_views import api_endpoints, api_guide, api_python_guide, operation_success, search_status


sitemaps = {
    "posts": PostSitemap,
}


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="site_index"),
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path("api/endpoints/", api_endpoints, name="api_endpoints"),
    path("api/guide/", api_guide, name="api_guide"),
    path("api/python-guide/", api_python_guide, name="api_python_guide"),
    path("search/status/", search_status, name="search_status"),
    path("operation-success/", operation_success, name="operation_success"),
    path("blog/", include("blog.urls", namespace="blog")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemaps",
    ),
    path("markdownx/", include(markdownx_urls)),
    path("users/", include("users.urls", namespace="users")),
    path("metrics", metrics_view, name="metrics"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
