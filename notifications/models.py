from django.db import models
from accounts.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('PAYMENT', 'Payment'),
        ('MAINTENANCE', 'Maintenance'),
        ('SYSTEM', 'System'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"