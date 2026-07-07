import subprocess
import unittest

from django.contrib.auth.models import User
from django.test import Client, TestCase
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

    def test_admin_login_required(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_admin_login_success(self):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Site administration")

    def test_admin_post_list_accessible(self):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get("/admin/blog/post/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Test Post")

    def test_admin_post_change_accessible(self):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(f"/admin/blog/post/{self.post.id}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Admin Test Post</h2>", html=True)

    def test_admin_post_delete(self):
        self.client.login(username="adminuser", password="adminpass123")
        post_id = self.post.id
        self.client.post(
            f"/admin/blog/post/{post_id}/delete/",
            {
                "post": post_id,
                "action": "delete_selected",
                "index": 0,
                "_selected_action": [post_id],
                "_save": "Save",
            },
            follow=True,
        )
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(id=post_id)


class DockerTest(TestCase):
    @unittest.skip("Docker tests must be run on the host machine")
    def test_db_container_running(self):
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=my_site_db", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("my_site_db", result.stdout.strip())

    @unittest.skip("Docker tests must be run on the host machine")
    def test_web_container_running(self):
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=my_site_web", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("my_site_web", result.stdout.strip())

    @unittest.skip("Docker tests must be run on the host machine")
    def test_container_health_check(self):
        result = subprocess.run(
            ["docker", "inspect", "my_site_web", "--format", "{{.State.Health.Status}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        health_status = result.stdout.strip()
        self.assertIn(health_status, ["healthy", "starting"])

    @unittest.skip("Docker tests must be run on the host machine")
    def test_docker_compose_project(self):
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("my_site_web", result.stdout)
        self.assertIn("my_site_db", result.stdout)
