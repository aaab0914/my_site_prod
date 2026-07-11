from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post


class AdminTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
        )
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="regularpass123",
        )
        self.post = Post.objects.create(
            title="Admin Test Post",
            slug="admin-test-post",
            body="This is a test post for admin.",
            author=self.regular_user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )

    def test_admin_post_list_accessible(self):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(reverse("admin:blog_post_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Test Post")

    def test_admin_post_change_accessible(self):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(reverse("admin:blog_post_change", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Test Post")

    def test_admin_post_delete(self):
        self.client.login(username="adminuser", password="adminpass123")
        post_id = self.post.id
        response = self.client.post(
            reverse("admin:blog_post_delete", args=[post_id]),
            {"post": post_id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(id=post_id).exists())
