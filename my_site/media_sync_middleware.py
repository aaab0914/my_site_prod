from .media_sync import maybe_sync_site_media


class MediaSyncMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/static/"):
            maybe_sync_site_media()
        return self.get_response(request)
