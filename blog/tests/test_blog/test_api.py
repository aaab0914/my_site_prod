from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from blog.models import Comment, Post


class BlogApiPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = User.objects.create_user(
            username="apiauthor",
            email="apiauthor@example.com",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="apiother",
            email="apiother@example.com",
            password="testpass123",
        )
        self.post = Post.objects.create(
            title="API Owned Post",
            slug="api-owned-post",
            body="Original body",
            author=self.author,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        self.post.tags.add("api")
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            email="apiauthor@example.com",
            body="Original comment",
            active=True,
        )

    def test_post_detail_api_rejects_non_author_patch(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            reverse("blog:api_post_detail", kwargs={"pk": self.post.pk}),
            {"title": "Hijacked Title"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "API Owned Post")

    def test_post_detail_api_allows_author_patch(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            reverse("blog:api_post_detail", kwargs={"pk": self.post.pk}),
            {"title": "Updated By Author"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated By Author")

    def test_comment_detail_api_rejects_patch(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(
            reverse("blog:api_comment_detail", kwargs={"pk": self.comment.pk}),
            {"body": "Changed comment"},
            format="json",
        )
        self.assertEqual(response.status_code, 405)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Original comment")

    def test_comment_detail_api_rejects_delete(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(reverse("blog:api_comment_detail", kwargs={"pk": self.comment.pk}))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())
