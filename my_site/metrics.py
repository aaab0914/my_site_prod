from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from django.http import Http404, HttpResponse


def metrics_view(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404("Not found.")
    return HttpResponse(generate_latest(REGISTRY), content_type=CONTENT_TYPE_LATEST)
