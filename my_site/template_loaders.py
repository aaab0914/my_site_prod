from pathlib import Path

from django.core.cache import caches
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
from django.template.loaders.filesystem import Loader as FilesystemLoader


TEMPLATE_CACHE_TIMEOUT = 60 * 60 * 24 * 30
TEMPLATE_CACHE_PREFIX = "template_html"
TARGET_TEMPLATE_DIRS = (
    str(Path("blog") / "templates"),
    str(Path("images") / "templates"),
    str(Path("my_site") / "templates"),
    str(Path("users") / "templates"),
)


def _normalize_path(path):
    return str(Path(path)).replace("\\", "/").lower()


def _should_cache_template(origin_name):
    normalized = _normalize_path(origin_name)
    return normalized.endswith(".html") and any(
        target in normalized for target in TARGET_TEMPLATE_DIRS
    )


def _build_cache_key(origin_name):
    template_path = Path(origin_name)
    try:
        mtime_ns = template_path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0
    normalized = _normalize_path(origin_name)
    return f"{TEMPLATE_CACHE_PREFIX}:{normalized}:{mtime_ns}"


class _RedisTemplateCacheMixin:
    cache_alias = "default"
    cache_timeout = TEMPLATE_CACHE_TIMEOUT

    def get_contents(self, origin):
        origin_name = getattr(origin, "name", "")
        if not origin_name or not _should_cache_template(origin_name):
            return super().get_contents(origin)

        cache = caches[self.cache_alias]
        cache_key = _build_cache_key(origin_name)
        cached_source = cache.get(cache_key)
        if cached_source is not None:
            return cached_source

        template_source = super().get_contents(origin)
        cache.set(cache_key, template_source, self.cache_timeout)
        return template_source


class RedisFilesystemLoader(_RedisTemplateCacheMixin, FilesystemLoader):
    pass


class RedisAppDirectoriesLoader(_RedisTemplateCacheMixin, AppDirectoriesLoader):
    pass
