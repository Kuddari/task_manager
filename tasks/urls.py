from django.urls import path
from . import views
from django.core.asgi import get_asgi_application
from .cosumers import NotificationConsumer
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('notifications/', views.notifications, name='notifications'),
    path('create_user/', views.create_user, name='create_user'),
    path('notifications/<int:pk>/read/', views.mark_notification_as_read, name='mark_notification_as_read'),
]

# WebSocket URL routing
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack( URLRouter(websocket_urlpatterns)),
})
