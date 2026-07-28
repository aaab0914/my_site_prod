from django.utils.text import slugify
from taggit.models import Tag


def normalize_tag_name(raw_value):
    value = "".join(str(raw_value or "").strip().split())
    if not value:
        return ""
    if not value.startswith("#"):
        value = f"#{value}"
    return value.lower()


def normalize_tag_slug(raw_value):
    normalized = normalize_tag_name(raw_value)
    return slugify(normalized.lstrip("#"))


def normalize_tag_list(values):
    normalized_tags = []
    seen = set()
    for value in values or []:
        normalized = normalize_tag_name(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_tags.append(normalized)
    return normalized_tags


def normalize_post_tags(post):
    if not getattr(post, "pk", None):
        return
    normalized_names = normalize_tag_list(tag.name for tag in post.tags.all())
    post.tags.set(normalized_names)


def normalize_all_tag_objects():
    tags = list(Tag.objects.order_by("id"))
    for tag in tags:
        normalized_name = normalize_tag_name(tag.name)
        if not normalized_name:
            continue
        normalized_slug = normalize_tag_slug(normalized_name)
        target = Tag.objects.filter(name=normalized_name).exclude(pk=tag.pk).order_by("id").first()
        if target:
            for tagged_item in list(tag.taggit_taggeditem_items.all()):
                exists = target.taggit_taggeditem_items.filter(
                    object_id=tagged_item.object_id,
                    content_type=tagged_item.content_type,
                ).exists()
                if exists:
                    tagged_item.delete()
                else:
                    tagged_item.tag = target
                    tagged_item.save(update_fields=["tag"])
            tag.delete()
            continue
        update_fields = []
        if tag.name != normalized_name:
            tag.name = normalized_name
            update_fields.append("name")
        if tag.slug != normalized_slug:
            tag.slug = normalized_slug
            update_fields.append("slug")
        if update_fields:
            tag.save(update_fields=update_fields)
