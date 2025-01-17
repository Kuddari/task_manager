from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from .utils import create_notification
from django.contrib.auth import authenticate, login, logout
from .cosumers import NotificationConsumer
from django.utils.timezone import now

def user_login(request):
    if request.method == 'POST':
        user_id = request.POST.get('username')  # User ID input
        password = request.POST.get('password')  # Password input

        # ตรวจสอบว่าผู้ใช้มีในฐานข้อมูลหรือยัง
        user = authenticate(request, username=user_id, password=password)

        if user is not None:
            # ถ้าผู้ใช้มีในระบบ ทำการล็อกอิน
            login(request, user)

            # Redirect ไปหน้าหลัก
            return redirect('project_list')  # เปลี่ยน 'project_list' เป็น URL ของหน้าหลักของคุณ

        else:
            # ตรวจสอบในตาราง UserLogin ก่อนว่ามีข้อมูลนี้อยู่หรือไม่
            if not UserLogin.objects.filter(username=user_id).exists():
                # ถ้าไม่มีข้อมูลในตาราง UserLogin แสดงว่าการล็อกอินไม่สำเร็จ
                return render(request, 'login.html', {
                    'error_message': 'ท่านกรอกชื่อผู้ใช้หรือรหัสผ่านผิด',  # "Your account is not authorized to log in."
                })

            # ถ้าผู้ใช้ไม่มีในฐานข้อมูล User ให้สร้างผู้ใช้ใหม่
            if not User.objects.filter(username=user_id).exists():
                # สร้างผู้ใช้ใหม่
                new_user = User(username=user_id)
                new_user.set_password(password)  # เข้ารหัสรหัสผ่าน
                new_user.save()

                # ล็อกอินผู้ใช้ใหม่ที่สร้าง
                user = authenticate(request, username=user_id, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('project_list')

            # ถ้าการสร้างผู้ใช้ใหม่ล้มเหลว แสดงข้อความข้อผิดพลาด
            return render(request, 'login.html', {
                'error_message': 'ชื่อผู้ใช้หรือรหัสผ่านผิด',
            })

    return render(request, 'login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')  # เปลี่ยน 'login' เป็นชื่อ URL ของหน้า Login


def project_list(request):

    return render(request, 'tasks/project_list.html')

def project(request):

    return render(request, 'tasks/project.html')

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

def employee(request):

    return render(request, 'tasks/employee.html')