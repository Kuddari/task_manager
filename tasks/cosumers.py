from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from channels.layers import get_channel_layer
import json

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user_id = self.scope["user"].id
        self.group_name = f"user_{self.user_id}_notifications"

        # Join the user's notification group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave the user's notification group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    def receive(self, text_data):
        # Handle incoming WebSocket messages (if needed)
        pass

    def send_notification(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"message": message}))

    @staticmethod
    def send_notification_to_group(user_id, message):
        group_name = f"user_{user_id}_notifications"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "send_notification", "message": message},
        )
