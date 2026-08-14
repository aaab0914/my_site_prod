# blog/templatetags/user_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def is_superuser(user):
    """
    检查用户是否是超级用户，返回相应的 HTML 标签
    """
    if user.is_authenticated and user.is_superuser:
        return mark_safe('<span style="color: #cc0000; font-weight: bold; font-size: 0.8em;">Superuser</span>')
    return ''