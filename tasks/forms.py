from django import forms
from .models import Project, Task
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    profile_picture = forms.ImageField(required=False, label="Profile Picture")

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'profile_picture']



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'due_date', 'priority', 'attachment']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pass the user to the form to filter members
        super().__init__(*args, **kwargs)

        if user:
            # Filter the assigned_to field to show only project members
            self.fields['assigned_to'].queryset = user.projects.all().values_list('members', flat=True)

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'due_date', 'priority', 'attachment']