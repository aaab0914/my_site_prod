from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token


class UserAccountDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")
        self.delete_url = reverse("users:account_delete")

    def test_delete_page_loads(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_account_success(self):
        user_id = self.user.id
        self.client.post(self.delete_url, {"confirm_delete": True})
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_account_requires_confirmation(self):
        user_id = self.user.id
        self.client.post(self.delete_url, {})
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_delete_account_get_only_shows_confirmation(self):
        user_id = self.user.id
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_delete_account_logs_user_out(self):
        response = self.client.post(self.delete_url, {"confirm_delete": True}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Back to Blog")

    def test_delete_requires_login(self):
        self.client.logout()
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)


class UsernameChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")
        self.url = reverse("users:username_change")

    def test_change_username_success(self):
        self.client.post(self.url, {"username": "newusername"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")

    def test_change_to_existing_username(self):
        User.objects.create_user(username="existinguser", password="pass")
        self.client.post(self.url, {"username": "existinguser"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_change_to_existing_username_case_insensitive(self):
        User.objects.create_user(username="ExistingUser", password="pass")
        response = self.client.post(self.url, {"username": "existinguser"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_change_username_rejects_invalid_characters(self):
        response = self.client.post(self.url, {"username": "bad name"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_change_username_rejects_empty_value(self):
        response = self.client.post(self.url, {"username": "   "}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_change_username_rejects_overlong_value(self):
        response = self.client.post(self.url, {"username": "a" * 151}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="logoutuser", password="testpass123")
        self.client.login(username="logoutuser", password="testpass123")
        self.url = reverse("users:logout")

    def test_logout_get_only_shows_confirmation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Confirm Logout")

    def test_logout_requires_post_to_end_session(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logged Out")
        follow_up = self.client.get(reverse("users:profile"))
        self.assertEqual(follow_up.status_code, 302)


class ApiTokenViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tokenuser", password="tokenpass123")
        self.url = reverse("users:api_token_manage")

    def test_api_token_manage_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_api_token_manage_shows_token_for_logged_in_user(self):
        self.client.login(username="tokenuser", password="tokenpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/api_token.html")
        token = Token.objects.get(user=self.user)
        self.assertContains(response, token.key)

class LoginLogoutIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='flowuser', password='flowpass123')
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')

    def test_login_creates_authenticated_session(self):
        response = self.client.post(self.login_url, {'username':'flowuser','password':'flowpass123'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_logout_clears_authenticated_session(self):
        self.client.login(username='flowuser', password='flowpass123')
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertNotIn('_auth_user_id', self.client.session)
