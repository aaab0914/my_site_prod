# my_site/middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """
    中间件：强制未登录用户只能访问首页、登录和注册页面。
    访问其他任何页面都跳转到登录页面。
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # 允许未登录用户访问的路径列表
        self.allowed_paths = [
            '/blog/',
            '/users/login/',
            '/users/register/',
        ]

    def __call__(self, request):
        # 如果用户已登录，正常处理请求
        if request.user.is_authenticated:
            return self.get_response(request)

        # 如果用户未登录，检查请求路径是否在允许列表中
        if request.path in self.allowed_paths:
            return self.get_response(request)

        # 否则，跳转到登录页面
        return redirect(reverse('users:login'))