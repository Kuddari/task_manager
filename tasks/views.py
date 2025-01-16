from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project, Task, Notification
from .forms import *
from .utils import create_notification
# views.py or where you handle logic (e.g., after creating a notification)
from .cosumers import NotificationConsumer



def project_list(request):
   

    return render(request, 'tasks/project_list.html')

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = project.tasks.all()
    return render(request, 'tasks/project_detail.html', {'project': project, 'tasks': tasks})


def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            # Notify assigned user
            create_notification(task.assigned_to, f"New task assigned: {task.title}")
            return redirect('project_detail', pk=task.project.pk)
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})


def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks/notifications.html', {'notifications': notifications})


def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

@login_required
def create_user(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create users.")
        return redirect('')  # Redirect to home page if not admin
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully!')
            return redirect('user_list')  # Redirect to user list or any page after creating a user
    else:
        form = UserCreateForm()
    
    return render(request, 'tasks/create_user.html', {'form': form})


def create_notification(user, message):
    # Create the notification in the database
    notification = Notification.objects.create(user=user, message=message)

    # Trigger the real-time notification
    NotificationConsumer.send_notification_to_group(user.id, message)