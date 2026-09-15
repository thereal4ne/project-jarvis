from django.urls import path
from . import views

urlpatterns = [
    path('auth/login', views.auth_login, name='auth-login'),
    path('command', views.api_command, name='api-command'),
    path('clipboard-summarize', views.api_clipboard_summarize, name='api-clipboard-summarize'),
    path('confirm-action', views.api_confirm_action, name='api-confirm-action'),
    path('history', views.api_history, name='api-history'),
    path('status', views.api_status, name='api-status'),
]
