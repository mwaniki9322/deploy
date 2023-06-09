import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AlertConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.id_2 = self.scope['url_route']['kwargs']['id_2']
        self.alert_group_name = 'user_alert_%s' % self.id_2

        if self.id_2 == self.scope['user'].id_2:

            # Join alert group
            await self.channel_layer.group_add(
                self.alert_group_name,
                self.channel_name
            )

            await self.accept()

        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave alert group
        await self.channel_layer.group_discard(
            self.alert_group_name,
            self.channel_name
        )

    # Receive message from alert group
    async def send_alert(self, event):
        alert = event['alert']

        # Send alert to WebSocket
        await self.send(text_data=json.dumps({
            'alert': alert
        }))
