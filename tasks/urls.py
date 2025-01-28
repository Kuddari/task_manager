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
    path('project_list/edit/<int:project_id>/', edit_project, name='edit_project'),
    path('delete_project/<int:project_id>/', delete_project, name='delete_project'),
    path('project_list/add-work/<int:pk>/', add_task, name='add_task'),

    path('project', tasks_list, name='project'),
    path('update-task-status/', update_task_status, name='update-task-status'),
    path('submit-task/', submit_task, name='submit-task'),
    path('get-task-details/<int:task_id>/', get_task_details, name='get_task_details'),
    path('projects/<int:pk>/', project_detail, name='project_detail'),
    path('tasks/create/', create_task, name='create_task'),
    path('edit_task/<int:task_id>/', edit_task, name='edit_task'),
    path('delete_task/<int:task_id>/', delete_task, name='delete_task'),
    path('notifications/', notifications, name='notifications'),
    path('create_user/', create_user, name='create_user'),
    path('notifications/<int:pk>/read/', mark_notification_as_read, name='mark_notification_as_read'),
    path('employee_list', employee_list, name='employee_list'),
    path('update_task_status/<int:task_id>/', update_task_status, name='update_task_status'),
    path('get_project_progress/<int:project_id>/', get_project_progress, name='get_project_progress'),


]

# WebSocket URL routing
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack( URLRouter(websocket_urlpatterns)),
})
