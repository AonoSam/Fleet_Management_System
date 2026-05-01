from django.db import models
from accounts.models import User
from vehicles.models import Vehicle


class Payment(models.Model):

    PAYMENT_TYPE_CHOICES = (
        ('FUEL', 'Fuel'),
        ('MAINTENANCE', 'Maintenance'),
        ('SALARY', 'Salary'),
        ('LOAN_REPAYMENT', 'Loan Repayment'),
        ('OTHER', 'Other'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    # 🔹 Who made/received payment
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'DRIVER'},
        null=True,
        blank=True
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # 🔹 PAYMENT CLASSIFICATION (IMPORTANT FOR REPORTS)
    payment_type = models.CharField(
        max_length=30,
        choices=PAYMENT_TYPE_CHOICES,
        default='OTHER'
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # 🔹 Link to Loan (VERY IMPORTANT for integration)
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_payments'
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    mpesa_receipt = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    # 🔹 Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # AUTO REFERENCE GENERATOR
    # -------------------------
    def save(self, *args, **kwargs):
        if not self.reference:
            import uuid
            self.reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"

        super().save(*args, **kwargs)

    def __str__(self):
        if self.driver:
            return f"{self.driver.username} - {self.amount}"
        return f"Company Payment - {self.amount}"