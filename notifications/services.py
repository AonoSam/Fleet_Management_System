from .models import Notification


# -------------------------
# CREATE NOTIFICATION
# -------------------------
def create_notification(user, message, notification_type='SYSTEM'):
    return Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type
    )


# -------------------------
# GET USER NOTIFICATIONS
# -------------------------
def get_user_notifications(user):
    return Notification.objects.filter(user=user)


# -------------------------
# UNREAD COUNT
# -------------------------
def get_unread_count(user):
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()


# -------------------------
# MARK ONE AS READ
# -------------------------
def mark_as_read(notification_id, user):
    notif = Notification.objects.filter(
        id=notification_id,
        user=user
    ).first()

    if notif:
        notif.is_read = True
        notif.save()

    return notif


# -------------------------
# MARK ALL AS READ
# -------------------------
def mark_all_as_read(user):
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)