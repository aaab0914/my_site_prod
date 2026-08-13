# Merged from package modules into a single file for simpler navigation.

# --- users/models/validators.py ---
from django.core.exceptions import ValidationError


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("图片大小不能超过5MB")

# --- users/models/profile.py ---
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse

from my_site.media_naming import static_media_upload_to


class Profile(models.Model):
    TOKEN_REGEN_COOLDOWN_DAYS = 5

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to=static_media_upload_to("avatars"), null=True, blank=True)
    last_avatar_change = models.DateTimeField(null=True, blank=True)
    last_token_generated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    def can_change_avatar(self):
        if not self.last_avatar_change:
            return True
        days_since_change = (timezone.now() - self.last_avatar_change).days
        return days_since_change >= 3

    def get_avatar_change_remaining_days(self):
        if not self.last_avatar_change:
            return 0
        days_since_change = (timezone.now() - self.last_avatar_change).days
        if days_since_change >= 3:
            return 0
        return 3 - days_since_change

    def can_regenerate_token(self):
        if self.user.is_staff or self.user.is_superuser:
            return True
        if not self.last_token_generated_at:
            return True
        days_since_generation = (timezone.now() - self.last_token_generated_at).days
        return days_since_generation >= self.TOKEN_REGEN_COOLDOWN_DAYS

    def get_token_regeneration_remaining_days(self):
        if self.user.is_staff or self.user.is_superuser:
            return 0
        if not self.last_token_generated_at:
            return 0
        days_since_generation = (timezone.now() - self.last_token_generated_at).days
        if days_since_generation >= self.TOKEN_REGEN_COOLDOWN_DAYS:
            return 0
        return self.TOKEN_REGEN_COOLDOWN_DAYS - days_since_generation

    def get_avatar_proxy_url(self):
        if not self.avatar:
            return ""
        version = int(self.last_avatar_change.timestamp()) if self.last_avatar_change else self.pk
        return f'{reverse("users:profile_avatar", args=[self.user.username])}?v={version}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()

# --- users/models/activity.py ---
from django.contrib.auth.models import User
from django.db import models


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

# --- users/models/preferences.py ---
from django.contrib.auth.models import User
from django.db import models


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    theme = models.CharField(
        max_length=20,
        default="light",
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System Default")],
    )
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"{self.user.username} Preferences"
