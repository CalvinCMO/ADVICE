"""
apps/accounts/middleware.py & backends.py combined support file.
"""
from django.utils import timezone


class LastActivityMiddleware:
    """Update user's last_activity on each authenticated request."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            # Only update every 5 minutes to avoid DB writes on every request
            if not request.user.last_activity or \
               (timezone.now() - request.user.last_activity).seconds > 300:
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])
        return response
