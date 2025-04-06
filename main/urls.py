from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('file-manager/', views.file_manager, name='file_manager'),
    path('file-view/', views.file_view, name='file_view'),
    path('create-file/', views.create_file, name='create_file'),
    path('delete-file/', views.delete_file, name='delete_file'),
    path('edit-file/', views.edit_file, name='edit_file'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('toggle-folder-visibility/', views.toggle_folder_visibility, name='toggle_folder_visibility'),
    path('delete-folder/', views.delete_folder, name='delete_folder'),
    path('move-file/', views.move_file, name='move_file'),
    path('move-file-ajax/', views.move_file_ajax, name='move_file_ajax'),
    path('snake/', views.snake_game, name='snake_game'),
    path('pong/', views.pong_game, name='pong_game'),
    path('hacking/', views.hacking_game, name='hacking_game'),
    path('blackjack/', views.blackjack_game, name='blackjack_game'),
]

handler404 = "main.views.custom_404"