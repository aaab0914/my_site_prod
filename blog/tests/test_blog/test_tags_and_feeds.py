from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from taggit.models import Tag

from blog.feeds import LatestPostsFeed
from blog.models import Post


class TagTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.post = Post.objects.create(
            title="Test Post with Tags",
            slug="test-post-with-tags",
            body="This is a test post with tags.",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )

    def test_add_tag_to_post(self):
        self.post.tags.add("django", "python", "testing")
        self.assertEqual(self.post.tags.count(), 3)
        self.assertTrue(self.post.tags.filter(name="django").exists())

    def test_query_posts_by_tag(self):
        self.post.tags.add("django", "python")
        tag = Tag.objects.get(name="django")
        posts = Post.published.filter(tags__in=[tag])
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts.first().title, "Test Post with Tags")

    def test_tag_slug_generation(self):
        tag = Tag.objects.create(name="Django REST Framework")
        self.assertEqual(tag.slug, "django-rest-framework")


class RSSFeedTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        for i in range(5):
            Post.objects.create(
                title=f"RSS Test Post {i}",
                slug=f"rss-test-post-{i}",
                body=f"This is RSS test post {i} body.",
                author=self.user,
                status=Post.Status.PUBLISHED,
                publish=timezone.now(),
            )

    def test_rss_feed_status_code(self):
        response = self.client.get(reverse("blog:post_feed"))
        self.assertEqual(response.status_code, 200)

    def test_rss_feed_content_type(self):
        response = self.client.get(reverse("blog:post_feed"))
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")

    def test_rss_feed_contains_posts(self):
        response = self.client.get(reverse("blog:post_feed"))
        self.assertContains(response, "RSS Test Post 0")
        self.assertContains(response, "RSS Test Post 4")

    def test_rss_feed_item_count(self):
        feed = LatestPostsFeed()
        items = feed.items()
        self.assertEqual(len(items), 5)


class SearchTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client.login(username="testuser", password="testpass123")
        Post.objects.create(
            title="Django Search Test",
            slug="django-search-test",
            body="This is a Django related post.",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        Post.objects.create(
            title="Python Search Test",
            slug="python-search-test",
            body="This is a Python related post.",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        Post.objects.create(
            title="JavaScript Search Test",
            slug="javascript-search-test",
            body="This is a JavaScript related post.",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )

    def test_search_by_body(self):
        response = self.client.get(reverse("blog:post_search"), {"query": "JavaScript"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JavaScript Search Test")

    def test_search_by_title(self):
        response = self.client.get(reverse("blog:post_search"), {"query": "Django"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Search Test")

    def test_search_empty_query(self):
        response = self.client.get(reverse("blog:post_search"), {"query": ""})
        self.assertEqual(response.status_code, 200)

    def test_search_no_results(self):
        response = self.client.get(reverse("blog:post_search"), {"query": "NonexistentTerm"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Found 0 results.")
        self.assertEqual(len(response.context["results"]), 0)
