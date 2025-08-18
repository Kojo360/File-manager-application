"""
ASGI config for backend project - Phase 3
WebSocket and real-time features support

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_phase3')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# WebSocket URL routing (Phase 3)
websocket_urlpatterns = [
    # Real-time analytics updates
    # path('ws/analytics/', consumers.AnalyticsConsumer.as_asgi()),
    # Real-time workflow updates
    # path('ws/workflows/', consumers.WorkflowConsumer.as_asgi()),
    # Real-time AI processing updates
    # path('ws/ai/', consumers.AIProcessingConsumer.as_asgi()),
]

# ASGI application with WebSocket support
application = ProtocolTypeRouter({
    # HTTP requests
    "http": django_asgi_app,
    
    # WebSocket connections (Phase 3)
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
