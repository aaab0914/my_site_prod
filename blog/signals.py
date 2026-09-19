import logging
import re
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Post, Comment
from .search import invalidate_search_caches

@receiver(post_save, sender=Post)
def post_saved_handler(sender, instance, created, **kwargs):
    logger = logging.getLogger(__name__)
    invalidate_search_caches()
    if created:
        logger.info("New post '%s' created by %s", instance.title, instance.author.username)
    else:
        logger.info("Post '%s' updated. Status: %s", instance.title, instance.status)

@receiver(pre_delete, sender=Post)
def post_deleted_handler(sender, instance, **kwargs):
    logger = logging.getLogger(__name__)
    invalidate_search_caches()
    logger.info("Post '%s' is being deleted by %s", instance.title, instance.author.username)

@receiver(pre_save, sender=User)
def validate_user_chars(sender, instance, **kwargs):
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    if chinese_pattern.search(instance.username):
        raise ValidationError('用户名不能包含中文字符')