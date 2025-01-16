from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)


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
    due_date = models.DateTimeField(null=True, blank=True)  # Optional deadline for the task
    priority = models.CharField(max_length=20, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')  # Task status
    is_overdue = models.BooleanField(default=False)  # Boolean to check if task is overdue
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)  # Add file attachment field

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override the save method to automatically check if the task is overdue and update the `is_overdue` field.
        """
        if self.due_date and self.due_date < timezone.now() and self.status != 'done':
            self.is_overdue = True
        else:
            self.is_overdue = False

        # Trigger notification when a new task is created and assigned
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.assigned_to:
            Notification.objects.create(
                user=self.assigned_to,
                message=f"A new task '{self.title}' has been assigned to you."
            )

    def update_status(self):
        """
        Updates the task's status and checks if the task is overdue.
        """
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
