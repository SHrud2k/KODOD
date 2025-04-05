from django.shortcuts import redirect
from django.urls import reverse

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