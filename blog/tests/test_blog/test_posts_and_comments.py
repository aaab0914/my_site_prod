from io import BytesIO

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from blog.models import AudioPost, Comment, Post
from blog.views import _cached_post_list_page, _cached_search_result_ids


class BlogRouteIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="routeuser",
            email="route@example.com",
            password="testpass123",
        )
        self.primary_post = Post.objects.create(
            title="Integrated Route Post",
            slug="integrated-route-post",
            body="Primary post body.",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        self.primary_post.tags.add("integration", "routing")
        for i in range(4):
            post = Post.objects.create(
                title=f"Similar Route Post {i}",
                slug=f"similar-route-post-{i}",
                body=f"Similar post body {i}.",
                author=self.user,
                status=Post.Status.PUBLISHED,
                publish=timezone.now() + timezone.timedelta(minutes=i + 1),
            )
            post.tags.add("integration")

    def test_blog_homepage_route(self):
        response = self.client.get(reverse("blog:all_posts_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post/all_posts_list.html")
        self.assertContains(response, "Integrated Route Post")

    def test_blog_feed_route_is_public(self):
        response = self.client.get(reverse("blog:post_feed"))
        self.assertEqual(response.status_code, 200)

    def test_blog_search_route_is_public(self):
        response = self.client.get(reverse("blog:post_search"), {"query": "Route"})
        self.assertEqual(response.status_code, 200)

    def test_blog_tag_route_is_public(self):
        response = self.client.get(reverse("blog:post_list_by_tag", kwargs={"tag_slug": "integration"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post/all_posts_list.html")

    def test_post_list_page_cache_returns_cached_ids(self):
        cache.clear()
        payload = _cached_post_list_page(1)
        self.assertTrue(payload["post_ids"])
        cache_key = "post_list:page:1:tag:all"
        self.assertEqual(cache.get(cache_key), payload)

    def test_post_search_result_ids_are_cached(self):
        cache.clear()
        result_ids = _cached_search_result_ids("Route")
        self.assertTrue(result_ids)
        cache_key = "post_search:query:route"
        self.assertEqual(cache.get(cache_key), result_ids)

    def test_blog_detail_route(self):
        response = self.client.get(self.primary_post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post/post_detail.html")
        self.assertContains(response, self.primary_post.title)

    def test_blog_create_route_requires_login(self):
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_blog_create_route_for_logged_in_user(self):
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post/create_post.html")

    def test_blog_create_post_submission(self):
        self.client.login(username="routeuser", password="testpass123")
        image = BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image, format="JPEG")
        image.name = "cover.jpg"
        image.seek(0)
        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "Created By Test",
                "body": "Created from integration test.",
                "tags": "integration,test",
                "cover_image": image,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(title="Created By Test").exists())
        self.assertContains(response, "Created By Test")

    def test_comment_post_requires_login(self):
        response = self.client.post(
            reverse("blog:post_comment", kwargs={"post_id": self.primary_post.id}),
            {"body": "Anonymous comment attempt"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_comment_post_submission_creates_comment(self):
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.post(
            reverse("blog:post_comment", kwargs={"post_id": self.primary_post.id}),
            {"body": "Integration comment"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Comment.objects.filter(post=self.primary_post, author=self.user, body="Integration comment").exists()
        )

    def test_edit_comment_rejects_non_owner(self):
        owner = User.objects.create_user(username="commentowner", password="testpass123")
        comment = Comment.objects.create(
            post=self.primary_post,
            author=owner,
            email="owner@example.com",
            body="Owner comment",
            active=True,
        )
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.post(
            reverse("blog:edit_comment", kwargs={"post_slug": self.primary_post.slug, "comment_id": comment.id}),
            {"body": "Malicious edit"},
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.body, "Owner comment")

    def test_delete_comment_rejects_non_owner(self):
        owner = User.objects.create_user(username="commentowner", password="testpass123")
        comment = Comment.objects.create(
            post=self.primary_post,
            author=owner,
            email="owner@example.com",
            body="Owner comment",
            active=True,
        )
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.post(
            reverse("blog:comment_delete", kwargs={"post_slug": self.primary_post.slug, "comment_id": comment.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_comment_delete_get_only_shows_confirmation(self):
        self.client.login(username="routeuser", password="testpass123")
        comment = Comment.objects.create(
            post=self.primary_post,
            author=self.user,
            email="route@example.com",
            body="Own comment",
            active=True,
        )
        response = self.client.get(
            reverse("blog:comment_delete", kwargs={"post_slug": self.primary_post.slug, "comment_id": comment.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())


class UploadValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="uploaduser",
            email="upload@example.com",
            password="testpass123",
        )
        self.client.login(username="uploaduser", password="testpass123")

    def test_post_create_requires_image_under_form_processing(self):
        oversized_file = SimpleUploadedFile("plain.txt", b"not-an-image", content_type="text/plain")
        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "Bad Upload",
                "body": "Should fail image validation.",
                "tags": "upload,test",
                "cover_image": oversized_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(title="Bad Upload").exists())

    def test_post_create_rejects_oversized_cover_image(self):
        oversized = SimpleUploadedFile(
            "cover.webp",
            b"RIFF1234WEBPVP8 " + (b"a" * (3 * 1024 * 1024 + 1)),
            content_type="image/webp",
        )
        response = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "Oversized Cover",
                "body": "Should fail size validation.",
                "tags": "upload,test",
                "cover_image": oversized,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(title="Oversized Cover").exists())
        self.assertContains(response, "Upload a valid image.")
