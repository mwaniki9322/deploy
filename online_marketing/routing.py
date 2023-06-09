from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from accounts.consumers import AlertConsumer
from custom_admin.consumers import AdminAlertConsumer

application = ProtocolTypeRouter({
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/users/<str:id_2>/alert/', AlertConsumer.as_asgi()),
            path('ws/admin-alert/', AdminAlertConsumer.as_asgi()),
        ])
    ),
})
