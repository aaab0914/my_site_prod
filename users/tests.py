from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Profile, UserActivity, UserPreference
from .forms import UserRegisterForm, UserLoginForm


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@example.com')

    def test_profile_created_on_user_creation(self):
        """Test that Profile is created when User is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str(self):
        """Test Profile string representation"""
        self.assertEqual(str(self.user.profile), 'testuser Profile')

    def test_can_change_avatar_first_time(self):
        """Test avatar change allowed on first change"""
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_can_change_avatar_within_3_days(self):
        """Test avatar change blocked within 3 days"""
        self.user.profile.last_avatar_change = timezone.now()
        self.user.profile.save()
        self.assertFalse(self.user.profile.can_change_avatar())

    def test_can_change_avatar_after_3_days(self):
        """Test avatar change allowed after 3 days"""
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=3)
        self.user.profile.save()
        self.assertTrue(self.user.profile.can_change_avatar())

    def test_avatar_change_remaining_days(self):
        """Test remaining days calculation"""
        self.user.profile.last_avatar_change = timezone.now() - timedelta(days=1)
        self.user.profile.save()
        self.assertEqual(self.user.profile.get_avatar_change_remaining_days(), 2)

    def test_user_activity_creation(self):
        """Test UserActivity model"""
        activity = UserActivity.objects.create(
            user=self.user,
            action='login',
            ip_address='127.0.0.1'
        )
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.action, 'login')

    def test_user_preference_creation(self):
        """Test UserPreference model"""
        pref = UserPreference.objects.create(user=self.user, theme='dark')
        self.assertEqual(pref.theme, 'dark')
        self.assertTrue(pref.email_notifications)


class UserRegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')

    def test_register_page_loads(self):
        """Test GET register page"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_user_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123',
            'password2': 'SecurePass123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(response.url, reverse('blog:all_posts_list'))

    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123',
            'password2': 'DifferentPass'
        }
        response = self.client.post(self.register_url, data)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.login_url = reverse('users:login')

    def test_login_page_loads(self):
        """Test GET login page"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """Test successful login"""
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        data = {'username': 'testuser', 'password': 'wrongpass'}
        response = self.client.post(self.login_url, data)
        self.assertNotIn('_auth_user_id', self.client.session)


class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_view_own_profile(self):
        """Test viewing own profile"""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user)

    def test_view_other_profile(self):
        """Test viewing other user's profile"""
        other_user = User.objects.create_user(username='otheruser', password='pass')
        response = self.client.get(reverse('users:profile_by_username', kwargs={'username': 'otheruser'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], other_user)

    def test_profile_not_found(self):
        """Test 404 for non-existent user"""
        response = self.client.get(reverse('users:profile_by_username', kwargs={'username': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)


class UserAccountDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.delete_url = reverse('users:account_delete')

    def test_delete_page_loads(self):
        """Test GET delete confirmation page"""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_account_success(self):
        """Test successful account deletion"""
        user_id = self.user.id
        response = self.client.post(self.delete_url, {'confirm_delete': True})
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_requires_login(self):
        """Test delete requires authentication"""
        self.client.logout()
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)


class UsernameChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('users:username_change')

    def test_change_username_success(self):
        """Test successful username change"""
        response = self.client.post(self.url, {'username': 'newusername'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_change_to_existing_username(self):
        """Test cannot change to existing username"""
        User.objects.create_user(username='existinguser', password='pass')
        response = self.client.post(self.url, {'username': 'existinguser'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')
