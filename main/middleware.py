from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Если пользователь не авторизован (нет сессионного ключа 'logged_in'),
    то разрешён только доступ к URL логина и URL, начинающимся на /static/ (для статики).
    Все остальные запросы перенаправляются на страницу логина.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # URL логина и разрешённые пути (например, для статики)
        self.allowed_paths = [reverse("login")]
    
    def __call__(self, request):
        # Разрешаем доступ к статическим файлам (если URL начинается с /static/)
        if request.path.startswith("/static/"):
            return self.get_response(request)
        
        # Если пользователь не авторизован и запрашиваемый путь не является разрешённым, редирект на логин
        if not request.session.get("logged_in") and request.path not in self.allowed_paths:
            return redirect("login")
        
        response = self.get_response(request)
        return response

class ClearRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the IP address and user agent
        ip = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Clear rate limit in these cases:
        # 1. When accessing login page with GET request
        # 2. When session is not active
        if (request.path == '/login/' and request.method == 'GET') or \
           not request.session.get('logged_in'):
            session_key = f'login_attempts_{ip}_{user_agent}'
            timestamp_key = f'login_timestamp_{ip}_{user_agent}'
            request.session.pop(session_key, None)
            request.session.pop(timestamp_key, None)
        
        response = self.get_response(request)
        return response