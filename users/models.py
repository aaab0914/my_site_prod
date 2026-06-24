# users/models.py
# ========================================
# Imports
# ========================================

from django.db import models
# models: Django's ORM module for defining database models

from django.contrib.auth.models import User
# User: The built-in user model

from django.db.models.signals import post_save
# post_save: Signal that is sent after a model instance is saved

from django.dispatch import receiver
# receiver: Decorator for connecting a signal to a function

from django.utils import timezone
# timezone: Django's timezone utilities for handling timezone-aware datetime operations

from django.core.exceptions import ValidationError


# ValidationError: Exception raised when data validation fails


def validate_image_size(image):
    if image.size > 3 * 1024 * 1024:
        raise ValidationError('图片大小不能超过3MB')


# ========================================
# Models
# ========================================

class Profile(models.Model):
    """
    Profile model extending the built-in User model.

    This model stores additional user information such as bio, location,
    birth date, and avatar. It also tracks the last time the avatar was
    changed to enforce a 3-day cooldown period.

    Attributes:
        user: One-to-one relationship with the User model.
        bio: A short biography of the user (optional).
        location: User's location (optional).
        birth_date: User's date of birth (optional).
        avatar: User's profile picture (optional).
        last_avatar_change: Timestamp of the last avatar change.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    last_avatar_change = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """
        Returns a human-readable string representation of the profile.
        """
        return f'{self.user.username} Profile'

    def can_change_avatar(self):
        """
        Checks if the user is allowed to change their avatar.

        Returns:
            bool: True if the user can change avatar, False otherwise.
        """
        if not self.last_avatar_change:
            return True
        days_since_change = (timezone.now() - self.last_avatar_change).days
        return days_since_change >= 3

    def get_avatar_change_remaining_days(self):
        """
        Calculates the number of days remaining until the user can change their avatar.

        Returns:
            int: Number of days remaining (0 if no restriction or already allowed).
        """
        if not self.last_avatar_change:
            return 0
        days_since_change = (timezone.now() - self.last_avatar_change).days
        if days_since_change >= 3:
            return 0
        return 3 - days_since_change


class UserActivity(models.Model):
    """
    UserActivity model for tracking user actions.

    This model logs user activities such as login, logout, and other actions
    for auditing and monitoring purposes.

    Attributes:
        user: Foreign key to the User who performed the action.
        action: Description of the action performed.
        ip_address: IP address from which the action was performed.
        timestamp: Time when the action was performed.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'

    def __str__(self):
        """
        Returns a human-readable string representation of the user activity.
        """
        return f'{self.user.username} - {self.action} - {self.timestamp}'


class UserPreference(models.Model):
    """
    UserPreference model for storing user preferences.

    This model stores user preferences such as theme selection and
    notification settings.

    Attributes:
        user: One-to-one relationship with the User model.
        theme: Selected theme preference ('light', 'dark', or 'system').
        email_notifications: Whether to receive email notifications.
        push_notifications: Whether to receive push notifications.
        comment_notifications: Whether to receive comment notifications.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default')
    ])
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        """
        Returns a human-readable string representation of the user preferences.
        """
        return f'{self.user.username} Preferences'


# ========================================
# Signals
# ========================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler that creates a Profile instance when a new User is created.

    This function is automatically called after a User instance is saved.
    If the user is newly created (created=True), a corresponding Profile
    instance is created automatically.

    Args:
        sender: The model class that sent the signal (User).
        instance: The actual User instance being saved.
        created: Boolean indicating whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler that ensures the Profile instance is saved when the User is saved.

    This function is automatically called after a User instance is saved.
    It ensures that the associated Profile is also saved, creating it if
    it doesn't exist.

    Args:
        sender: The model class that sent the signal (User).
        instance: The actual User instance being saved.
        **kwargs: Additional keyword arguments.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()