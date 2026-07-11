from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from blog.models import VideoPost
from blog.views import _prime_video_list_cache


class VideoRouteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="videoadmin",
            email="videoadmin@example.com",
            password="testpass123",
        )
        self.user = User.objects.create_user(
            username="videouser",
            email="videouser@example.com",
            password="testpass123",
        )

    def create_video(self, title="Original Video", file_name="clip.mp4", content=b"video-bytes"):
        return VideoPost.objects.create(
            uploaded_by=self.superuser,
            title=title,
            description="Original description",
            video_file=SimpleUploadedFile(file_name, content, content_type="video/mp4"),
        )

    def test_video_list_route_is_public(self):
        video = self.create_video()
        cache.clear()
        cached_items = _prime_video_list_cache()
        self.assertTrue(any(item["id"] == video.id and item["title"] == video.title for item in cached_items))
        response = self.client.get(reverse("blog:video_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/video/video_list.html")

    def test_video_upload_redirects_anonymous_user_home_with_no_store(self):
        response = self.client.get(reverse("blog:video_upload"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("blog:all_posts_list"))
        self.assertEqual(response["Cache-Control"], "no-store, no-cache, must-revalidate, max-age=0, private")

    def test_video_list_guest_actions_point_to_login(self):
        video = self.create_video(title="Love")
        cache.clear()
        _prime_video_list_cache()

        response = self.client.get(reverse("blog:video_list"))

        self.assertContains(response, f'{reverse("users:login")}?next={reverse("blog:video_detail", kwargs={"pk": video.pk})}')
        self.assertNotContains(response, 'Upload More')

    def test_video_file_proxy_is_public(self):
        video = self.create_video(title="Love")

        response = self.client.get(reverse("blog:video_file_proxy", kwargs={"pk": video.pk}))

        self.assertEqual(response.status_code, 200)

    def test_video_detail_redirects_regular_user_home(self):
        video = self.create_video()
        self.client.login(username="videouser", password="testpass123")
        response = self.client.get(reverse("blog:video_detail", kwargs={"pk": video.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("blog:all_posts_list"))

    def test_superuser_can_edit_video_title_only(self):
        video = self.create_video()
        original_name = video.video_file.name
        self.client.login(username="videoadmin", password="testpass123")
        response = self.client.post(
            reverse("blog:video_edit", kwargs={"pk": video.pk}),
            {
                "title": "Updated Video Title",
                "description": "Original description",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        video.refresh_from_db()
        self.assertEqual(video.title, "Updated Video Title")
        self.assertEqual(video.video_file.name, original_name)

    def test_superuser_can_replace_video_file(self):
        video = self.create_video(content=b"old-video")
        self.client.login(username="videoadmin", password="testpass123")
        replacement = SimpleUploadedFile("replacement.mp4", b"new-video", content_type="video/mp4")
        response = self.client.post(
            reverse("blog:video_edit", kwargs={"pk": video.pk}),
            {
                "title": "Original Video",
                "description": "Updated description",
                "video_file": replacement,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        video.refresh_from_db()
        self.assertIn("replacement", video.get_video_filename())
        self.assertEqual(video.description, "Updated description")

    def test_superuser_can_delete_video(self):
        video = self.create_video()
        self.client.login(username="videoadmin", password="testpass123")
        response = self.client.post(reverse("blog:video_delete", kwargs={"pk": video.pk}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(VideoPost.objects.filter(pk=video.pk).exists())

    def test_video_delete_invalidates_list_cache(self):
        video = self.create_video()
        _prime_video_list_cache()
        self.assertTrue(any(item["id"] == video.id for item in cache.get("video_list:items") or []))

        self.client.login(username="videoadmin", password="testpass123")
        response = self.client.post(reverse("blog:video_delete", kwargs={"pk": video.pk}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(VideoPost.objects.filter(pk=video.pk).exists())
        self.assertEqual(cache.get("video_list:items"), [])

    def test_video_edit_refreshes_list_cache_title(self):
        video = self.create_video()
        _prime_video_list_cache()
        self.client.login(username="videoadmin", password="testpass123")

        response = self.client.post(
            reverse("blog:video_edit", kwargs={"pk": video.pk}),
            {
                "title": "Cache Updated Title",
                "description": "Original description",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        cached_items = cache.get("video_list:items") or []
        self.assertTrue(any(item["id"] == video.id and item["title"] == "Cache Updated Title" for item in cached_items))

    def test_video_incremental_prime_rebuilds_full_cache_when_cache_is_empty(self):
        older_video = self.create_video(title="Love", file_name="love.mp4")
        newer_video = self.create_video(title="New Clip", file_name="new.mp4")
        cache.delete("video_list:items")
        cache.delete("video_list:ids")

        cached_items = _prime_video_list_cache([newer_video])

        cached_ids = [item["id"] for item in cached_items]
        self.assertIn(older_video.id, cached_ids)
        self.assertIn(newer_video.id, cached_ids)
