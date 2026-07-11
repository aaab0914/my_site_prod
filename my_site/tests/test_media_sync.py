import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from blog.models import AudioPost, Comment, Post
from images.models import ImagePost
from my_site.media_sync import sync_site_media


def _write_media_file(path, content=b"test"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@override_settings(MEDIA_SYNC_INTERVAL_SECONDS=0, MEDIA_SYNC_ENABLED=True)
class MediaSyncTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="media-sync-tests-")
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.user = User.objects.create_user(username="tester", password="secret123")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_sync_deletes_required_record_when_media_file_is_missing(self):
        image_post = ImagePost.objects.create(
            title="gallery",
            image="posts/2026/07/07/gallery.jpg",
            uploaded_by=self.user,
        )

        result = sync_site_media()

        self.assertFalse(ImagePost.objects.filter(id=image_post.id).exists())
        self.assertTrue(
            any(
                action["type"] == "deleted_record" and action["model"] == "images.ImagePost"
                for action in result["missing_actions"]
            )
        )

    def test_sync_clears_optional_field_when_media_file_is_missing(self):
        post = Post.objects.create(
            title="post-title",
            slug="post-title",
            author=self.user,
            body="body",
            cover_image="posts/2026/07/07/cover.jpg",
        )

        result = sync_site_media()
        post.refresh_from_db()

        self.assertFalse(post.cover_image)
        self.assertTrue(
            any(
                action["type"] == "cleared_field"
                and action["model"] == "blog.Post"
                and action["field"] == "cover_image"
                for action in result["missing_actions"]
            )
        )

    def test_sync_moves_orphan_files_to_trash(self):
        orphan_file = Path(self.media_root) / "comments" / "2026" / "07" / "07" / "orphan.jpg"
        _write_media_file(orphan_file)

        result = sync_site_media()

        self.assertFalse(orphan_file.exists())
        self.assertTrue(
            any(item["from"] == "comments/2026/07/07/orphan.jpg" for item in result["trashed_files"])
        )
        self.assertTrue(any(Path(settings.BASE_DIR, item["to"]).exists() for item in result["trashed_files"]))

    def test_sync_keeps_referenced_files(self):
        audio_path = Path(self.media_root) / "audio" / "2026" / "07" / "07" / "track.mp3"
        _write_media_file(audio_path)
        audio = AudioPost.objects.create(
            audio_file="audio/2026/07/07/track.mp3",
            uploaded_by=self.user,
            music_name="track",
        )

        result = sync_site_media()
        audio.refresh_from_db()

        self.assertTrue(audio.audio_file.name.endswith("track.mp3"))
        self.assertTrue(audio_path.exists())
        self.assertEqual(result["trashed_files"], [])

    def test_sync_clears_comment_image_without_deleting_comment(self):
        post = Post.objects.create(
            title="comment-post",
            slug="comment-post",
            author=self.user,
            body="body",
        )
        comment = Comment.objects.create(
            post=post,
            author=self.user,
            email="tester@example.com",
            body="comment body",
            image="comments/2026/07/07/comment.jpg",
        )

        sync_site_media()
        comment.refresh_from_db()

        self.assertFalse(comment.image)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())




class AuditMiddlewareTests(TestCase):
    def test_audit_middleware_ignores_authenticated_objects_without_primary_key(self):
        from unittest.mock import patch

        from my_site.audit_middleware import AuditLoggingMiddleware

        class UnsavedAuthenticatedUser:
            is_authenticated = True
            pk = None

        request = type(
            "Request",
            (),
            {
                "method": "GET",
                "path": "/audit-probe/",
                "META": {"REMOTE_ADDR": "127.0.0.1"},
                "user": UnsavedAuthenticatedUser(),
            },
        )()
        response = type("Response", (), {"status_code": 200})()

        middleware = AuditLoggingMiddleware(lambda req: response)

        with patch("my_site.audit_middleware.AuditLog.objects.create") as mocked_create:
            returned = middleware(request)

        self.assertIs(returned, response)
        mocked_create.assert_called_once()
        self.assertIsNone(mocked_create.call_args.kwargs["user"])
