def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0}

    from circulation.models import Notification

    return {
        "unread_notifications_count": Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()
    }
