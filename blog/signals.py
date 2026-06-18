from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Post
from .models import Comment
from django.contrib.auth.models import User
import re

# Signal: triggered when a Post instance is saved (created or updated)
@receiver(post_save, sender=Post)
def post_saved_handler(sender, instance, created, **kwargs):
    if created:
        print(f"New post '{instance.title}' created by {instance.author.username}")
        # You can add custom logic here: send notification, update cache, etc.
    else:
        print(f"Post '{instance.title}' updated. Status: {instance.status}")

# Signal: triggered before a Post instance is deleted
@receiver(pre_delete, sender=Post)
def post_deleted_handler(sender, instance, **kwargs):
    print(f"Post '{instance.title}' is being deleted by {instance.author.username}")
    # You can add clean-up logic here: delete images, log action, etc.


@receiver(pre_save, sender=User)
def validate_user_chars(sender, instance, **kwargs):
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    # 验证用户名
    if chinese_pattern.search(instance.username):
        raise ValidationError('用户名不能包含中文字符')

    # 验证密码（注意：密码是哈希后的，无法直接验证）
    # 需要在密码设置时验证，这里无法验证