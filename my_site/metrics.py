from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from django.http import HttpResponse


def metrics_view(request):
    return HttpResponse(generate_latest(REGISTRY), content_type=CONTENT_TYPE_LATEST)
