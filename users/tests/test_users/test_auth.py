from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse


class UserRegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("users:register")

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_user_success(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertEqual(response.url, reverse("blog:all_posts_list"))

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "SecurePass123",
            "password2": "DifferentPass",
        }
        self.client.post(self.register_url, data)
        self.assertFalse(User.objects.filter(username="newuser").exists())


class UserLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.login_url = reverse("users:login")
        cache.clear()

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_wrong_password(self):
        self.client.post(self.login_url, {"username": "testuser", "password": "wrongpass"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_is_rate_limited_after_repeated_failures(self):
        data = {"username": "testuser", "password": "wrongpass"}
        for _ in range(5):
            self.client.post(self.login_url, data)
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 429)


class UserRouteIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_route_is_available_for_blog_redirects(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)

    def test_register_route_is_available_for_blog_redirects(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)

    def test_profile_route_requires_login_for_own_profile(self):
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 302)
