from django.db import models
from drivers.models import Driver


class Loan(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cleared', 'Cleared'),
    ]

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    loan_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.driver} - {self.amount}"

    # =========================
    # CALCULATE TOTAL PAID
    # =========================
    def total_paid(self):
        return sum(r.amount_paid for r in self.repayments.all())

    # =========================
    # BALANCE REMAINING
    # =========================
    def balance(self):
        return float(self.amount) - float(self.total_paid())

    # =========================
    # AUTO CHECK IF CLEARED
    # =========================
    def is_cleared(self):
        return self.total_paid() >= float(self.amount)


class LoanRepayment(models.Model):

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name="repayments"
    )

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan} - {self.amount_paid}"