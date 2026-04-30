from django.db import models
from accounts.models import User
from vehicles.models import Vehicle


class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    driver = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'DRIVER'})
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver.username} - {self.amount}"