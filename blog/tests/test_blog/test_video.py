from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from blog.models import VideoPost


class VideoRouteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="videoadmin",
            email="videoadmin@example.com",
            password="VideoPass123!",
        )
        self.user = User.objects.create_user(
            username="videouser",
            email="videouser@example.com",
            password="VideoPass123!",
        )

    def create_video(self, title="Original Video", file_name="clip.mp4", content=b"video-bytes"):
        return VideoPost.objects.create(
            uploaded_by=self.superuser,
            title=title,
            description="Original description",
            video_file=SimpleUploadedFile(file_name, content, content_type="video/mp4"),
        )

    def test_video_list_route_is_public(self):
        self.create_video()
        response = self.client.get(reverse("blog:video_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/video/video_list.html")

    def test_video_upload_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("blog:video_upload"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("blog:all_posts_list"))

    def test_video_file_proxy_is_public(self):
        video = self.create_video(title="Love")
        response = self.client.get(reverse("blog:video_file_proxy", kwargs={"pk": video.pk}))
        self.assertEqual(response.status_code, 200)
