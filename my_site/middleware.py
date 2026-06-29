# my_site/middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    中间件：保留为轻量占位，不再承担业务访问控制。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
