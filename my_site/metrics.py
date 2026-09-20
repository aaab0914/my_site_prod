from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest


def metrics_view(request):
    return HttpResponse(generate_latest(REGISTRY), content_type=CONTENT_TYPE_LATEST)
