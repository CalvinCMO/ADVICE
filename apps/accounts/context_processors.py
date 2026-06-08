def notifications_processor(request):
    try:
        if request.user.is_authenticated:
            from apps.messaging.models import Notification
            unread_count = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
            recent_notifications = Notification.objects.filter(
                recipient=request.user
            ).order_by('-created_at')[:5]
            return {
                'unread_notifications_count': unread_count,
                'recent_notifications': recent_notifications,
            }
    except Exception:
        pass
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
