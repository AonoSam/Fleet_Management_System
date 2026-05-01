from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal
from accounts.models import User


# -------------------------
# LOAN MODEL
# -------------------------
class Loan(models.Model):

    LOAN_TYPE_CHOICES = (
        ('DRIVER', 'Driver Loan'),
        ('BANK', 'Bank Loan'),
    )

    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role': 'DRIVER'}
    )

    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    purpose = models.CharField(max_length=255, null=True, blank=True)

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loan_requests"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_loans"
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-issued_date']

    # -------------------------
    # VALIDATION
    # -------------------------
    def clean(self):

        if self.loan_type == 'DRIVER' and not self.driver:
            raise ValidationError("Driver loan must have a driver.")

        if self.loan_type == 'BANK' and self.driver:
            raise ValidationError("Bank loan must NOT have a driver.")

        if self.amount <= 0:
            raise ValidationError("Loan amount must be greater than zero.")

        if self.interest_rate < 0:
            raise ValidationError("Interest rate cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------
    # FINANCIAL CORE
    # -------------------------
    def interest_amount(self):
        return (self.amount * self.interest_rate) / Decimal('100')

    def total_payable(self):
        return self.amount + self.interest_amount()

    def total_paid(self):
        return self.repayments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

    def balance(self):
        return self.total_payable() - self.total_paid()

    def is_fully_paid(self):
        return self.balance() <= 0

    def update_status(self):
        if self.is_fully_paid() and self.status != 'PAID':
            self.status = 'PAID'
            self.save(update_fields=['status'])

    # -------------------------
    # PROFIT RULES (SAFE + CONSISTENT)
    # -------------------------
    def interest_income(self):
        if self.loan_type != 'DRIVER':
            return Decimal('0.00')

        total = self.total_payable()
        if total == 0:
            return Decimal('0.00')

        return (self.interest_amount() * self.total_paid()) / total

    def interest_expense(self):
        if self.loan_type != 'BANK':
            return Decimal('0.00')

        total = self.total_payable()
        if total == 0:
            return Decimal('0.00')

        return (self.interest_amount() * self.total_paid()) / total

    def __str__(self):
        if self.loan_type == 'DRIVER' and self.driver:
            return f"{self.driver.username} - KSh {self.amount}"
        return f"Bank Loan - KSh {self.amount}"


# -------------------------
# LOAN REPAYMENT (🔥 FIX FOR YOUR IMPORT ERROR)
# -------------------------
class LoanRepayment(models.Model):

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='repayments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.loan.update_status()

    def __str__(self):
        return f"{self.loan} - KSh {self.amount}"