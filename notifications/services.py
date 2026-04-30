from .models import Notification


def create_notification(user, message, notification_type='SYSTEM'):
    return Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type
    )


def get_user_notifications(user):
    return Notification.objects.filter(user=user).order_by('-created_at')


def get_unread_count(user):
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_as_read(notification_id, user):
    notif = Notification.objects.filter(id=notification_id, user=user).first()
    if notif:
        notif.is_read = True
        notif.save()
    return notif


def mark_all_as_read(user):
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)