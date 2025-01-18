from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from .utils import create_notification
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from .cosumers import NotificationConsumer
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.http import JsonResponse

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


def project_lists(request):

    return render(request, 'tasks/project_list.html')

@login_required
def add_project(request):
    if request.method == 'POST':
        # 1) Gather the posted form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        # If the <select> can select multiple members, use getlist('members')
        # If it's single selection, use get('members')
        member_ids = request.POST.getlist('members')  # or request.POST.get('members')
        
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        # Convert date strings (dd/mm/yyyy) to Python datetime
        date_format = "%d/%m/%Y"
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, date_format)
            except ValueError:
                start_date = None
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, date_format)
            except ValueError:
                end_date = None

        # is_active from hidden input (default to True if not found)
        is_active_str = request.POST.get('is_active', 'true')
        is_active = (is_active_str.lower() == 'true')
        
        # 2) Create the project
        new_project = Project.objects.create(
            name=name,
            description=description,
            created_by=request.user,   # The currently logged-in user
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        
        # 3) Assign members (one or many). If your select is single, you'll have just one ID in member_ids.
        for mid in member_ids:
            try:
                user_member = User.objects.get(pk=mid)
                new_project.members.add(user_member)
            except User.DoesNotExist:
                pass  # Handle or ignore invalid user IDs
        
        # 4) Redirect (or show success message) after creation
        return redirect('project_list')  # Change to your desired URL name

    # If GET, show the form (or the page containing the modal) with a list of possible members
    return redirect('project_list')
   
def project_list(request):
    """
    Show all projects (no selected project).
    The modal will be hidden initially.
    """
    projects = Project.objects.all()
    members = User.objects.all()
    # 'selected_project' not set here
    return render(request, 'tasks/project_lists.html', {
        'projects': projects,
        'members': members
    })

def project_detail(request, pk):
    """
    Show the same template, but with 'selected_project'
    so the detail modal is OPENED automatically.
    """
    projects = Project.objects.all()
    project = get_object_or_404(Project, pk=pk)
    tasks = project.tasks.all()
    members = project.members.all()

    # e.g. maybe tasks = project.tasks.all() if you have tasks
    # For now, just pass 'project'
    return render(request, 'tasks/project_lists.html', {
        'projects': projects,          # grid
        'members': members,
        'tasks' : tasks,
        'selected_project': project    # indicates we want the modal shown
    })


def add_task(request, pk):
    """
    Handle the POST form submission to create a new Task associated with a project.
    """
    project = get_object_or_404(Project, pk=pk)  # Get the project by ID

    if request.method == 'POST':
        # Gather form data
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        assigned_id = request.POST.get('assigned_to')
        due_date_str = request.POST.get('due_date')
        status_val = request.POST.get('status', 'to_do')  # Default to 'to_do'

        # Convert due_date from string to datetime
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d/%m/%Y")
            except ValueError:
                # Handle invalid date format if needed
                pass

        # Resolve the assigned User
        assigned_user = None
        if assigned_id:
            assigned_user = User.objects.filter(pk=assigned_id).first()

        # Create the Task
        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_user,
            created_by=request.user,  # Currently logged-in user
            project=project,  # Associate the task with the project
            due_date=due_date,
            status=status_val,
        )

        # Redirect to the project detail page
        return redirect('project_detail', pk=pk)

    # For non-POST requests, redirect back to the project detail page
    return redirect('project_detail', pk=pk)

def add_tasks(request, project_id):
    """
    Handle the POST form submission from 'WorkModal-Popup' to create a new Task.
    """
    if request.method == 'POST':
        # 1) Get the project
        project = get_object_or_404(Project, pk=project_id)

        # 2) Gather form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_id = request.POST.get('assigned_to')
        due_date_str = request.POST.get('due_date')  # Format: dd/mm/yyyy
        status_val = request.POST.get('status', 'to_do')

        # 3) Convert due_date from string to datetime
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%d/%m/%Y")
            except ValueError:
                due_date = None

        # 4) Resolve the assigned User
        assigned_user = None
        if assigned_id:
            try:
                assigned_user = User.objects.get(pk=assigned_id)
            except User.DoesNotExist:
                assigned_user = None

        # 5) Create the Task
        new_task = Task.objects.create(
            title=title,
            description=description or "",
            assigned_to=assigned_user,
            created_by=request.user,
            due_date=due_date,
            status=status_val,
            priority="Medium",
            project=project,  # Associate with the selected project
        )

        # 6) Handle file attachment, if provided
        attachment_file = request.FILES.get('attachment')
        if attachment_file:
            new_task.attachment = attachment_file
            new_task.save(update_fields=['attachment'])

        # 7) Redirect back to the project detail view
        return redirect('project_detail', pk=project_id)

    # If it's a GET request, redirect to the project list
    return redirect('project_list')

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

def employee_list(request):
    # Fetch all users from the database
    employees = User.objects.all()
    
    # Pass the user list to the template
    return render(request, 'tasks/employee.html', {'employees': employees})

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        position = request.POST.get('position')
        faculty = request.POST.get('faculty')
        major = request.POST.get('major')
        profile_picture = request.FILES.get('profile_picture')

        # Create a new user using Django's create_user for proper password hashing
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name or "",
            last_name=last_name or ""
        )
        user.position = position
        user.faculty = faculty
        user.major = major

        if profile_picture:
            user.profile_picture = profile_picture
        
        user.save()

        # (Optional) Automatically log the user in
        # login(request, user)

        # Redirect to some page after successful registration
        return redirect('employee_list')

    
    # If it's a GET request, you can return a template (if needed)
    return redirect('employee_list')