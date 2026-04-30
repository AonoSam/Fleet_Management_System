from django.db import models
from accounts.models import User


class Loan(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('PAID', 'Paid'),
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'DRIVER'}
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ FIXED: corrected spelling + required field
    purpose = models.CharField(max_length=255)

    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.driver.username} - {self.amount} ({self.status})"