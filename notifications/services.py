from .models import Notification


def create_notification(user, title, message, notification_type="system"):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )


def get_user_notifications(user):
    return Notification.objects.filter(user=user).order_by('-created_at')


def mark_as_read(notification_id):
    notification = Notification.objects.get(id=notification_id)
    notification.is_read = True
    notification.save()
    return notification