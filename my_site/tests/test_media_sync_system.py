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


@override_settings(ROOT_URLCONF="my_site.tests.test_media_sync_system")
class MediaSyncMiddlewareTests(SimpleTestCase):
    def test_requests_work_without_removed_media_sync_middleware(self):
        response = self.client.get("/media-sync-probe/")
        self.assertEqual(response.status_code, 200)

    def test_static_requests_are_unaffected_without_removed_media_sync_middleware(self):
        response = self.client.get("/static/app.css")
        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_SYNC_INTERVAL_SECONDS=10, MEDIA_SYNC_ENABLED=False)
class MediaSyncThrottleTests(SimpleTestCase):
    def setUp(self):
        patcher = patch(
            "my_site.media_sync.sync_site_media",
            return_value={"enabled": False, "missing_actions": [], "trashed_files": []},
        )
        self.sync_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_maybe_sync_site_media_returns_none_when_automatic_sync_is_disabled(self):
        result = maybe_sync_site_media()
        self.assertIsNone(result)
        self.sync_mock.assert_not_called()

    def test_maybe_sync_site_media_does_not_use_legacy_throttle_state(self):
        result = maybe_sync_site_media()
        self.assertIsNone(result)
        self.sync_mock.assert_not_called()


class MediaSyncTaskTests(SimpleTestCase):
    def test_sync_site_media_task_delegates_to_sync_function(self):
        result = sync_site_media_task()
        self.assertFalse(result["enabled"])
        self.assertIn("only when users delete objects", result["reason"])
