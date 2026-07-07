"""
Signal handlers for the blog and user applications.

This module defines Django signals that trigger automatic actions
when certain model events occur, such as saving or deleting a post,
or validating user input before save.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

import re
# re: Regular expression module, used to match and validate string patterns.

from django.db.models.signals import post_save, pre_delete, pre_save
# post_save: Signal sent after a model instance is saved.
# pre_delete: Signal sent before a model instance is deleted.
# pre_save: Signal sent before a model instance is saved.

from django.dispatch import receiver
# receiver: Decorator that connects a function to a specific signal.

from django.core.exceptions import ValidationError
# ValidationError: Exception raised when data validation fails.

from django.contrib.auth.models import User
# User: Django's built-in user model.

from .models import Post, Comment


# Post: The main blog post model.
# Comment: User comments attached to posts.


# =============================================================================
# SIGNAL: POST SAVE (Post)
# =============================================================================

@receiver(post_save, sender=Post)
def post_saved_handler(sender, instance, created, **kwargs):
    """
    Signal handler triggered after a Post is saved.

    Args:
        sender: The model class that sent the signal (Post).
        instance: The actual Post instance being saved.
        created: Boolean indicating whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        # Log a message when a new post is created.
        print(f"New post '{instance.title}' created by {instance.author.username}")
        # You can add custom logic here: send notification, update cache, etc.
    else:
        # Log a message when an existing post is updated.
        print(f"Post '{instance.title}' updated. Status: {instance.status}")


# =============================================================================
# SIGNAL: PRE DELETE (Post)
# =============================================================================

@receiver(pre_delete, sender=Post)
def post_deleted_handler(sender, instance, **kwargs):
    """
    Signal handler triggered before a Post is deleted.

    Args:
        sender: The model class that sent the signal (Post).
        instance: The Post instance about to be deleted.
        **kwargs: Additional keyword arguments.
    """
    # Log a message before the post is deleted.
    print(f"Post '{instance.title}' is being deleted by {instance.author.username}")
    # You can add clean-up logic here: delete images, log action, etc.


# =============================================================================
# SIGNAL: PRE SAVE (User)
# =============================================================================

@receiver(pre_save, sender=User)
def validate_user_chars(sender, instance, **kwargs):
    """
    Signal handler triggered before a User is saved.
    Validates that the username does not contain Chinese characters.

    Args:
        sender: The model class that sent the signal (User).
        instance: The User instance about to be saved.
        **kwargs: Additional keyword arguments.

    Raises:
        ValidationError: If the username contains Chinese characters.
    """
    # Compile a regex pattern to match Chinese characters.
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    # Validate that the username does not contain Chinese characters.
    if chinese_pattern.search(instance.username):
        raise ValidationError('用户名不能包含中文字符')

    # Note: Password validation is not performed here because the password
    # is already hashed by the time this signal is triggered. Password
    # validation should be handled at the form or model level during creation.

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                         blog/signals.py                                    │
# │                    (Signal Handlers)                                       │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  re                           │  django.db.models.signals                  │
# │  django.dispatch              │  ├─ post_save                             │
# │  └─ receiver                  │  ├─ pre_delete                           │
# │  django.core.exceptions       │  └─ pre_save                             │
# │  └─ ValidationError           │  django.contrib.auth.models               │
# │  .models                      │  └─ User                                 │
# │  ├─ Post                      │                                         │
# │  └─ Comment                   │                                         │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │          Signal Handler Functions              │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   post_saved_handler │  │   post_deleted_handler │  │   validate_user_    │
# │   (Function)         │  │   (Function)         │  │   chars             │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Connects to:         │  │ Connects to:         │  │ Connects to:         │
# │   post_save, Post    │  │   pre_delete, Post   │  │   pre_save, User     │
# │                      │  │                      │  │                      │
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   Log post creation  │  │   Log post deletion  │  │   Validate that      │
# │   or update events   │  │   events             │  │   usernames do not   │
# │                      │  │                      │  │   contain Chinese    │
# │ Args:                │  │ Args:                │  │   characters         │
# │   sender (Post)      │  │   sender (Post)      │  │                      │
# │   instance (Post)    │  │   instance (Post)    │  │ Args:                │
# │   created (bool)     │  │   **kwargs           │  │   sender (User)      │
# │   **kwargs           │  │                      │  │   instance (User)    │
# │                      │  │                      │  │   **kwargs           │
# │ Logic:               │  │ Logic:               │  │                      │
# │   Print message      │  │   Print message      │  │ Logic:               │
# │   with title/author  │  │   with title/author  │  │   Check username     │
# │                      │  │                      │  │   against regex      │
# │                      │  │                      │  │   Raise Validation   │
# │                      │  │                      │  │   Error if match    │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘