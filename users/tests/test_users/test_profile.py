from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Comment, Post


class UserProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_view_own_profile(self):
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], self.user)

    def test_view_other_profile(self):
        other_user = User.objects.create_user(username="otheruser", password="pass")
        response = self.client.get(reverse("users:profile_by_username", kwargs={"username": "otheruser"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], other_user)

    def test_view_other_profile_hides_draft_posts_and_inactive_comments(self):
        other_user = User.objects.create_user(username="otheruser", password="pass")
        published_post = Post.objects.create(
            title="Published profile post",
            slug="published-profile-post",
            body="Visible post body",
            author=other_user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        published_post.tags.add("profile")
        Post.objects.create(
            title="Draft profile post",
            slug="draft-profile-post",
            body="Hidden draft body",
            author=other_user,
            status=Post.Status.DRAFT,
            publish=timezone.now(),
        )
        Comment.objects.create(post=published_post, author=other_user, email="other@example.com", body="Visible comment", active=True)
        Comment.objects.create(post=published_post, author=other_user, email="other@example.com", body="Hidden comment", active=False)
        response = self.client.get(reverse("users:profile_by_username", kwargs={"username": "otheruser"}))
        self.assertEqual(response.status_code, 200)
        posts = list(response.context["posts"])
        comments = list(response.context["comments"])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "Published profile post")
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].body, "Visible comment")

    def test_view_own_profile_keeps_draft_posts_and_all_comments(self):
        published_post = Post.objects.create(
            title="Own published post",
            slug="own-published-post",
            body="Visible post body",
            author=self.user,
            status=Post.Status.PUBLISHED,
            publish=timezone.now(),
        )
        published_post.tags.add("profile")
        Post.objects.create(
            title="Own draft post",
            slug="own-draft-post",
            body="Draft body",
            author=self.user,
            status=Post.Status.DRAFT,
            publish=timezone.now(),
        )
        Comment.objects.create(post=published_post, author=self.user, email="test@example.com", body="Active own comment", active=True)
        Comment.objects.create(post=published_post, author=self.user, email="test@example.com", body="Inactive own comment", active=False)
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["posts"].count(), 2)
        self.assertEqual(response.context["comments"].count(), 2)

    def test_profile_not_found(self):
        response = self.client.get(reverse("users:profile_by_username", kwargs={"username": "nonexistent"}))
        self.assertEqual(response.status_code, 404)

    def test_profile_edit_post_updates_non_file_fields(self):
        response = self.client.post(
            reverse("users:profile_edit"),
            {"bio": "Updated bio", "location": "Shanghai", "birth_date": "2000-01-01"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Updated bio")
        self.assertEqual(self.user.profile.location, "Shanghai")

    def test_profile_edit_avatar_upload_respects_login_flow(self):
        avatar = SimpleUploadedFile("avatar.jpg", b"avatar-bytes", content_type="image/jpeg")
        response = self.client.post(
            reverse("users:profile_edit"),
            {"bio": "Avatar update", "location": "Beijing", "birth_date": "2001-02-03", "avatar": avatar},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_rejects_disallowed_avatar_type(self):
        avatar = SimpleUploadedFile("avatar.webp", b"RIFF1234WEBPVP8 ", content_type="image/webp")
        response = self.client.post(
            reverse("users:profile_edit"),
            {"bio": "Avatar update", "location": "Beijing", "birth_date": "2001-02-03", "avatar": avatar},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload a valid image.")
