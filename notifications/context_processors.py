from .services import get_user_notifications, get_unread_count


def notification_context(request):
    if request.user.is_authenticated:

        notifications = get_user_notifications(request.user)[:10]  # 🔥 limit for navbar
        unread_count = get_unread_count(request.user)

    else:
        notifications = []
        unread_count = 0

    return {
        "notifications": notifications,
        "unread_count": unread_count
    }