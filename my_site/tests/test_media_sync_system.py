from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path

from my_site.media_sync import maybe_sync_site_media
from my_site.tasks import sync_site_media_task


def _media_sync_probe_view(request):
    return HttpResponse("ok")


urlpatterns = [
    path("media-sync-probe/", _media_sync_probe_view),
]


@override_settings(
    ROOT_URLCONF="my_site.tests.test_media_sync_system",
    MEDIA_SYNC_INTERVAL_SECONDS=10,
    MIDDLEWARE=[
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "my_site.media_sync_middleware.MediaSyncMiddleware",
    ],
)
class MediaSyncMiddlewareTests(SimpleTestCase):
    def test_middleware_allows_normal_requests_without_sync_side_effects(self):
        response = self.client.get("/media-sync-probe/")

        self.assertEqual(response.status_code, 200)

    def test_middleware_allows_static_requests_without_sync_side_effects(self):
        response = self.client.get("/static/app.css")

        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_SYNC_INTERVAL_SECONDS=10, MEDIA_SYNC_ENABLED=True)
class MediaSyncThrottleTests(SimpleTestCase):
    def setUp(self):
        patcher = patch("my_site.media_sync.sync_site_media", return_value={"missing_actions": [], "trashed_files": []})
        self.sync_mock = patcher.start()
        self.addCleanup(patcher.stop)
        reset_patcher = patch("my_site.media_sync._LAST_SYNC_AT", 0.0)
        reset_patcher.start()
        self.addCleanup(reset_patcher.stop)

    def test_maybe_sync_site_media_runs_when_interval_has_elapsed(self):
        with patch("my_site.media_sync.time.monotonic", return_value=100.0):
            result = maybe_sync_site_media()

        self.assertEqual(result, {"missing_actions": [], "trashed_files": []})
        self.sync_mock.assert_called_once_with()

    def test_maybe_sync_site_media_skips_when_interval_not_elapsed(self):
        with patch("my_site.media_sync.time.monotonic", side_effect=[100.0, 100.0]):
            first_result = maybe_sync_site_media()

        with patch("my_site.media_sync.time.monotonic", return_value=105.0):
            second_result = maybe_sync_site_media()

        self.assertEqual(first_result, {"missing_actions": [], "trashed_files": []})
        self.assertIsNone(second_result)
        self.sync_mock.assert_called_once_with()


class MediaSyncTaskTests(SimpleTestCase):
    def test_sync_site_media_task_delegates_to_sync_function(self):
        expected = {"missing_actions": [{"type": "cleared_field"}], "trashed_files": [{"from": "a", "to": "b"}]}

        with patch("my_site.tasks.sync_site_media", return_value=expected) as sync_mock:
            result = sync_site_media_task()

        self.assertEqual(result, expected)
        sync_mock.assert_called_once_with()
