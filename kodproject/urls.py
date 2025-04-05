from django.urls import path, include

urlpatterns = [
    path('', include('main.urls')),
]

handler404 = "main.views.custom_404"