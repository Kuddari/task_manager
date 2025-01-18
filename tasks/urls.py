from django.urls import path
from .views import *
from django.core.asgi import get_asgi_application
from .cosumers import NotificationConsumer
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


urlpatterns = [
    path('', user_login, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', user_logout, name='logout'),
    path('project_list', project_list, name='project_list'),
    path('project_list/add/', add_project, name='add_project'),
    path('project', project_lists, name='project'),
    path('projects/<int:pk>/', project_detail, name='project_detail'),
    path('tasks/create/', create_task, name='create_task'),
    path('notifications/', notifications, name='notifications'),
    path('create_user/', create_user, name='create_user'),
    path('notifications/<int:pk>/read/', mark_notification_as_read, name='mark_notification_as_read'),
    path('employee_list', employee_list, name='employee_list'),

]

# WebSocket URL routing
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack( URLRouter(websocket_urlpatterns)),
})
