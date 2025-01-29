from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import *
from .forms import *
from .utils import create_notification
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import default_storage
from .cosumers import NotificationConsumer
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
import json
from django.views.decorators.csrf import csrf_exempt  # Add this import
import logging

logger = logging.getLogger(__name__)


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
            return redirect('project')  # เปลี่ยน 'project_list' เป็น URL ของหน้าหลักของคุณ

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
                    return redirect('project')

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

def edit_project(request, project_id):
    # Get the project to edit
    project = get_object_or_404(Project, pk=project_id)
    print("Project:", project)
    # Get all possible members (users)
    if request.method == 'POST':
        # 1) Gather the posted form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        member_ids = request.POST.getlist('edit_members')  # Extract member IDs from the form
        print("Member IDs from Form:", member_ids)  # Debugging

        
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
        
        # 2) Update the project fields
        project.name = name
        project.description = description
        project.start_date = start_date
        project.end_date = end_date
        project.is_active = is_active
        project.save()
        
        # 3) Update members
        # Clear existing members
        # Update project members
        project.members.clear()  # Clear existing members
        print("Members after clearing:", project.members.all())  # Debugging
        
        for mid in member_ids:
            try:
                user_member = User.objects.get(pk=int(mid))  # Convert ID to int
                print(f"Adding User ID {mid} ({user_member}) to Project")  # Debugging
                project.members.add(user_member)
            except User.DoesNotExist:
                print(f"User ID {mid} does not exist")  # Handle invalid user IDs
        
                print("Members after saving:", project.members.all())  # Debugging
                pass  # Handle or ignore invalid user IDs
        
        # 4) Redirect (or show success message) after updating
        return redirect('project_list')  # Change to your desired URL name

    # If GET, return to project list or show the form with pre-filled data
    return redirect('project_list')  # Change to your desired URL name

def delete_project(request, project_id):
    # Ensure the request is a POST request
    if request.method == 'POST':
        # Get the project to delete
        project = get_object_or_404(Project, pk=project_id)

        # Save the project name for the confirmation message
        project_name = project.name

        # Delete the project
        project.delete()

        # Add a success message
        messages.success(request, f"The project '{project_name}' was successfully deleted.")

        # Redirect to the project list or another appropriate page
        return redirect('project_list')  # Replace with the name of your project list view

    # If not a POST request, redirect back to the project list
    return redirect('project_list')  # Replace with the appropriate redirect


def project_list(request):
    """
    Show all projects with task completion statistics.
    """
    projects = Project.objects.annotate(
        total_tasks=Count('tasks'),
        completed_tasks=Count('tasks', filter=Q(tasks__status='done')),
    )

    # Calculate combined total and completed tasks across all projects
    total_tasks_all = sum(project.total_tasks for project in projects)
    completed_tasks_all = sum(project.completed_tasks for project in projects)

    # Calculate overall completion percentage
    overall_completion_percentage = (
        (completed_tasks_all / total_tasks_all * 100) if total_tasks_all > 0 else 0
    )
    # Add completion percentage for each project
    for project in projects:
        project.completion_percentage = (
            (project.completed_tasks / project.total_tasks * 100)
            if project.total_tasks > 0 else 0
        )

    members = User.objects.all()

    project_members = {
        project.id: list(project.members.values_list('id', flat=True))
        for project in projects
    }


    return render(request, 'tasks/project_lists.html', {
        'projects': projects,
        'members': members,
        'project_members': project_members,  # Pass project member data
        'overall_completion_percentage': overall_completion_percentage,  # Pass the completion percentage
    })

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = project.tasks.all()
    members = project.members.all()

    # Get filters from request
    member_filter = request.GET.get('member')
    status_filter = request.GET.get('status')

    # Convert member_filter to an integer (if it's not "all" or None)
    if member_filter and member_filter != "all":
        try:
            member_filter = int(member_filter)
        except ValueError:
            member_filter = None

    # Debugging
    print(f"Member Filter (after conversion): {member_filter}")

    # Apply filters
    if member_filter:
        tasks = tasks.filter(assigned_to_id=member_filter)
    if status_filter and status_filter != "all":
        tasks = tasks.filter(status=status_filter)

    # Calculate completion percentage
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='done').count()
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    project.completion_percentage = round(completion_percentage, 2)

    return render(request, 'tasks/project_lists.html', {
        'projects': Project.objects.all(),
        'members': members,
        'tasks': tasks,
        'selected_project': project,
        'member_filter': member_filter,
        'status_filter': status_filter,
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

def edit_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        # Get form data
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')

        # Convert the due_date from dd/mm/yyyy to yyyy-mm-dd
        due_date_str = request.POST.get('due_date')  # Input from form
        if due_date_str:
            try:
                # Convert to datetime object
                due_date = datetime.strptime(due_date_str, "%d/%m/%Y").date()
                task.due_date = due_date
            except ValueError:
                return HttpResponse("Invalid date format. Please use DD/MM/YYYY.", status=400)

        # Update the status
        task.status = request.POST.get('status')

        # Assign the member
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            task.assigned_to_id = assigned_to_id
        
        # Handle file attachment
        if 'attachment' in request.FILES:
            task.attachment = request.FILES['attachment']

        # Save the task
        task.save()

        # Redirect to the task list or project detail
        return redirect('project_detail', pk=task.project_id)

    # Redirect back to the project detail if not a POST request
    return redirect('project_detail', pk=task.project_id)

def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        # Delete the task
        task.delete()
        # Redirect to the project detail page or task list
        return redirect('project_detail', pk=task.project_id)

    # Redirect if not a POST request
    return redirect('project_detail', pk=task.project_id)

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

@login_required
def edit_employee(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')

        # Check if employee_id exists
        if not employee_id:
            return JsonResponse({'error': 'Employee ID is missing'}, status=400)

        # Retrieve employee safely
        employee = get_object_or_404(User, id=employee_id)

        # Update employee fields
        employee.username = request.POST.get('username', employee.username)
        employee.first_name = request.POST.get('first_name', employee.first_name)
        employee.last_name = request.POST.get('last_name', employee.last_name)
        employee.position = request.POST.get('position', employee.position)
        employee.faculty = request.POST.get('faculty', employee.faculty)
        employee.major = request.POST.get('major', employee.major)
        
        # Handle profile picture update
        if 'profile_picture' in request.FILES:
            # Delete old profile picture if exists
            if employee.profile_picture:
                default_storage.delete(employee.profile_picture.path)

            # Save new profile picture
            employee.profile_picture = request.FILES['profile_picture']

        # Update password only if provided
        password = request.POST.get('password')
        if password:
            employee.set_password(password)

        # Save changes
        employee.save()

        return redirect(employee_list)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def delete_employee(request):
    """
    View to delete an employee using AJAX.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Get JSON data from request
            employee_id = data.get('employee_id')

            if not employee_id:
                return JsonResponse({'error': 'Employee ID is missing'}, status=400)

            employee = get_object_or_404(User, id=employee_id)
            employee.delete()
            return JsonResponse({'success': True, 'message': 'Employee deleted successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def tasks_list(request):
    tasks = Task.objects.all()
    overdue_filter = request.GET.get('overdue')  # Get the 'overdue' query parameter
    status_filter = None  # Initialize status_filter to None
    is_checked_filter = request.GET.get('is_checked')  # Get the 'is_checked' query parameter

    if overdue_filter == 'true':  # If 'overdue=true' is specified
        tasks = tasks.filter(is_overdue=True, assigned_to=request.user)  # Filter only overdue tasks
    elif is_checked_filter == 'false':  # Filter for 'to_check' tasks (is_checked=False and status='done')
        tasks = tasks.filter(is_checked=False, status='done', created_by=request.user)
    else:
        # Apply the status filter only when 'overdue' or 'is_checked' is not active
        status_filter = request.GET.get('status', 'to_do')  # Default to 'to_do'
        if status_filter:
            tasks = tasks.filter(status=status_filter, assigned_to=request.user)  # Filter by status
    
    # Calculate counts for each task status
    counts = {
        'to_do': Task.objects.filter(status='to_do', assigned_to=request.user).count(),
        'in_progress': Task.objects.filter(status='in_progress', assigned_to=request.user).count(),
        'done': Task.objects.filter(status='done', assigned_to=request.user).count(),
        'overdue': Task.objects.filter(is_overdue=True, assigned_to=request.user).count(),  # Count overdue tasks
        'to_check': Task.objects.filter(status='done', is_checked=False, created_by=request.user).count(),  # Count tasks to check
    }

    return render(request, 'tasks/project_list.html', {
        'tasks': tasks,
        'status_filter': status_filter,
        'overdue_filter': overdue_filter,
        'is_checked_filter': is_checked_filter,
        'counts': counts,
    })

@csrf_exempt
def update_task_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug('Received data: %s', data)  # Log incoming data
            task_id = data.get('task_id')
            status = data.get('status')
            new_description = data.get('description', '').strip()  # Get new description if provided

            if not task_id or not status:
                return JsonResponse({'success': False, 'error': 'Missing task_id or status'})

            task = Task.objects.get(id=task_id)
            task.status = status
            if new_description:
                task.description = new_description
            task.save()

            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            logger.error('Task not found for ID: %s', task_id)
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except json.JSONDecodeError:
            logger.error('Invalid JSON received')
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            logger.error('Error: %s', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        logger.error('Invalid request method: %s', request.method)
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

def submit_task(request): 
    if request.method == 'POST':
        try:
            task_id = request.POST.get('task_id')
            url_input = request.POST.get('urlInput')
            details_input = request.POST.get('detailsInput')
            file_upload = request.FILES.get('fileUpload')

            # Debugging logs
            print(f"Task ID: {task_id}")
            print(f"URL Input: {url_input}")
            print(f"Details Input: {details_input}")
            print(f"File Upload: {file_upload}")

            # Fetch the task
            task = Task.objects.get(id=task_id)

            # Update the task fields
            task.status = 'done'
            task.url = url_input
            task.details = details_input

            # Handle file upload
            if file_upload:
                file_path = default_storage.save(f'uploads/{file_upload.name}', file_upload)
                task.attachment = file_path  # Update the attachment field

            task.save()

            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            print(f"Error: {e}")  # Debug unexpected errors
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_task_details(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        data = {
            'file_url': task.attachment.url if task.attachment else None,
            'url': task.url,
            'title': task.title,
            'details': task.details,
            'description': task.description,
            'created_by': task.created_by.get_full_name() if task.created_by else "Unknown",
            'status': task.status,
        }
        return JsonResponse(data)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    
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

def get_project_progress(request, project_id):
    try:
        project = Project.objects.annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='done'))
        ).get(pk=project_id)

        # Calculate completion percentage
        total_tasks = project.total_tasks or 1  # Avoid division by zero
        completion_percentage = (project.completed_tasks / total_tasks) * 100

        return JsonResponse({
            'success': True,
            'project_id': project.id,
            'completion_percentage': round(completion_percentage, 2)
        })
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)

@csrf_exempt
def update_task_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON body
            task_id = data.get('task_id')  # Get task_id from request body
            status = data.get('status')  # Get status from request body

            # Validate inputs
            if not task_id or not status:
                return JsonResponse({'success': False, 'error': 'Missing task_id or status'})

            # Fetch and update the task
            task = Task.objects.get(id=task_id)
            task.status = status
            task.save()

            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def update_task_check_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            action = data.get('action')  # Action: "approve" or "edit"

            # Validate task_id
            if not task_id:
                return JsonResponse({'success': False, 'error': 'Task ID is required'})

            # Get the task
            task = Task.objects.get(id=task_id)

            if action == 'approve':
                task.is_checked = True  # Set is_checked to True
            elif action == 'edit':
                task.status = 'to_do'  # Change status to 'to_do'
                task.to_edit = True  # Assume `to_edit` is a field in your model
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})

            task.save()  # Save changes to the database
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})