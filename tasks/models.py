from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import hashlib

class User(AbstractUser):
    """
    AbstractUser already provides fields like:
      - username
      - password
      - is_staff
      - is_active
      - is_superuser
      - first_name
      - last_name
      - email
      - last_login
      - date_joined
    """
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        null=True, 
        blank=True
    )
    profile = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="ประวัติ"
    )
    position = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="ตำแหน่ง"
    )
    faculty = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="คณะ"
    )
    major = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="สาขา"
    )

    def __str__(self):
        return self.username


class UserLogin(models.Model):
    """
    WARNING: Storing plain-text passwords is not secure.
    This model is for demonstration or controlled environments.
    """
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Plain-text password (not recommended)
    login_time = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)

    def __str__(self):
        return f"Login Attempt for {self.username} at {self.login_time}"

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    members = models.ManyToManyField(User, related_name='projects')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Track if the project is active or not

    def __str__(self):
        return self.name

    def is_overdue(self):
        if self.end_date and self.end_date < timezone.now():
            return True
        return False

class Task(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    is_overdue = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)

    # NEW FIELD: Tracks the last time the status was updated
    status_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override the save method to automatically check if the task is overdue
        and update the `is_overdue` field.
        """
        """from django.utils import timezone

        # Overdue logic
        if self.due_date and self.due_date < timezone.now() and self.status != 'done':
            self.is_overdue = True
        else:
            self.is_overdue = False"""

        # Detect if this is a new object vs an update
        is_new = self.pk is None

        # Store old status to check if status changed
        old_status = None
        if not is_new:
            # Fetch the existing version from DB to compare statuses
            old_task = Task.objects.filter(pk=self.pk).first()
            if old_task:
                old_status = old_task.status

        super().save(*args, **kwargs)

        # If newly created and assigned_to is set, create a notification
        if is_new and self.assigned_to:
            Notification.objects.create(
                user=self.assigned_to,
                message=f"A new task '{self.title}' has been assigned to you."
            )

        # Check if status changed (not new, and the status is different)
        if not is_new and old_status is not None and old_status != self.status:
            # Update status_updated_at
            self.status_updated_at = timezone.now()
            super().save(update_fields=['status_updated_at'])

    def update_status(self, new_status):
        """
        Updates the task's status, sets is_overdue accordingly,
        and updates the status_updated_at timestamp when status changes.
        """
        from django.utils import timezone

        # If the status changed, update the timestamp
        if self.status != new_status:
            self.status = new_status
            self.status_updated_at = timezone.now()

        # Overdue logic
        if self.status == 'done':
            self.is_overdue = False
        elif self.due_date and self.due_date < timezone.now() and self.status != 'done':
            self.is_overdue = True
        else:
            self.is_overdue = False
        
        self.save()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
