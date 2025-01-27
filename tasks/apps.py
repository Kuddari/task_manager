import threading
import time
from django.apps import AppConfig

class TasksAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        # Start the background thread
        updater_thread = threading.Thread(target=self.run_overdue_updater, daemon=True)
        updater_thread.start()

    def run_overdue_updater(self):
        from django.db import connection
        from django.utils.timezone import now
        from tasks.models import Task

        while True:
            print("Checking and updating overdue tasks...")
            with connection.cursor():  # Ensure the DB connection is ready
                overdue_tasks = Task.objects.filter(due_date__lt=now(), status__in=['to_do', 'in_progress'])
                overdue_tasks.update(is_overdue=True)
                Task.objects.filter(is_overdue=True, status='done').update(is_overdue=False)

            time.sleep(300)  # Wait 5 minutes
