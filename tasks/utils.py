# tasks/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
def create_notification(user, message):
    # Save notification to the database
    notification = Notification.objects.create(user=user, message=message)
    
    # Send real-time notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}_notifications",
        {
            "type": "send_notification",
            "message": message,
        }
    )
