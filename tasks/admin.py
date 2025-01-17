from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(UserLogin)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Notification)