from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from users.models import Profile, UserActivity, UserPreference


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

    def test_profile_created_on_user_creation(self):
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), "testuser Profile")

    def test_can_change_avatar_first_time(self):
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_can_change_avatar_within_3_days(self):
        self.user.profile.last_avatar_change = timezone.now()
        self.user.profile.save()
        self.assertFalse(self.user.profile.can_change_avatar())

    def test_can_change_avatar_after_3_days(self):
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=3)
        self.user.profile.save()
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_avatar_change_remaining_days(self):
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=1)
        self.user.profile.save()
        self.assertEqual(self.user.profile.get_avatar_change_remaining_days(), 2)

    def test_user_activity_creation(self):
        activity = UserActivity.objects.create(user=self.user, action="login", ip_address="127.0.0.1")
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, "login")

    def test_user_preference_creation(self):
        pref = UserPreference.objects.create(user=self.user, theme="dark")
        self.assertEqual(pref.theme, "dark")
        self.assertTrue(pref.email_notifications)
