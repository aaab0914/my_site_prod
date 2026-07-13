from pathlib import Path

from django.core.cache import cache


MEDIA_CACHE_TIMEOUT = 300


def media_file_exists(field_file):
    if not field_file:
        return False
    try:
        file_name = getattr(field_file, "name", "") or ""
        if not file_name:
            return False
        storage = getattr(field_file, "storage", None)
        if storage and storage.exists(file_name):
            return True
    except Exception:
        pass
    try:
        return Path(field_file.path).is_file()
    except (ValueError, OSError):
        return False


def filter_existing_media_instances(queryset, field_name, limit=None):
    items = []
    for instance in queryset:
        if media_file_exists(getattr(instance, field_name, None)):
            items.append(instance)
        if limit is not None and len(items) >= limit:
            break
    return items


def valid_media_ids(queryset, field_name, limit=None):
    return [instance.id for instance in filter_existing_media_instances(queryset, field_name, limit=limit)]


def merge_new_ids(cache_key, new_ids, timeout=MEDIA_CACHE_TIMEOUT):
    cached_ids = cache.get(cache_key) or []
    if new_ids or cached_ids:
        merged = list(new_ids) + [item_id for item_id in cached_ids if item_id not in new_ids]
        cache.set(cache_key, merged, timeout)
        return merged
    return []


def prime_id_cache(cache_key, queryset, field_name, new_items=None, timeout=MEDIA_CACHE_TIMEOUT):
    if new_items is not None:
        new_ids = [item.id for item in new_items if media_file_exists(getattr(item, field_name, None))]
        merged = merge_new_ids(cache_key, new_ids, timeout=timeout)
        if merged:
            return merged
    ids = valid_media_ids(queryset, field_name)
    cache.set(cache_key, ids, timeout)
    return ids


def prime_serialized_list_cache(ids_key, items_key, queryset, serializer, new_items=None, timeout=MEDIA_CACHE_TIMEOUT):
    if new_items is not None:
        cached_items = cache.get(items_key)
        if cached_items:
            existing_ids = {item['id'] for item in cached_items}
            fresh = [serializer(item) for item in new_items if item.id not in existing_ids]
            if fresh:
                fresh_ids = {item['id'] for item in fresh}
                merged = fresh + [item for item in cached_items if item['id'] not in fresh_ids]
                cache.set(items_key, merged, timeout)
                cache.set(ids_key, [item['id'] for item in merged], timeout)
                return merged
            return cached_items
    ids = list(queryset.order_by('-created').values_list('id', flat=True))
    items = [serializer(item) for item in queryset.filter(id__in=ids)]
    items.sort(key=lambda item: ids.index(item['id']))
    cache.set(items_key, items, timeout)
    cache.set(ids_key, [item['id'] for item in items], timeout)
    return items


def invalidate_cache_keys(*cache_keys):
    for cache_key in cache_keys:
        cache.delete(cache_key)


def invalidate_public_view_caches(*cache_keys):
    if not cache_keys:
        return
    for cache_key in cache_keys:
        if cache_key:
            cache.delete(cache_key)
