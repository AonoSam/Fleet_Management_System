from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from .models import Loan, LoanRepayment


# =========================
# GET ALL LOANS
# =========================
def get_all_loans(loan_type=None, status=None):

    loans = Loan.objects.select_related('driver')

    if not status:
        loans = loans.exclude(status='REJECTED')

    if loan_type:
        loans = loans.filter(loan_type=loan_type)

    if status:
        loans = loans.filter(status=status)

    return loans.order_by('-issued_date')


# =========================
# DRIVER LOANS
# =========================
def get_driver_loans(driver):

    return Loan.objects.filter(
        loan_type='DRIVER',
        driver=driver
    ).order_by('-issued_date')


# =========================
# BANK LOANS (COMPANY)
# =========================
def get_bank_loans():

    return Loan.objects.filter(
        loan_type='BANK'
    ).order_by('-issued_date')


# =========================
# SINGLE LOAN
# =========================
def get_loan(loan_id):

    return Loan.objects.select_related('driver').get(id=loan_id)


# ======================================================
# DRIVER INTEREST RULE ENGINE
# ======================================================
def calculate_driver_interest(amount):

    amount = Decimal(amount)

    if amount <= 999:
        return Decimal('1.00')
    elif amount <= 3000:
        return Decimal('2.12')
    elif amount <= 5000:
        return Decimal('2.76')
    elif amount <= 10000:
        return Decimal('3.01')
    elif amount <= 20000:
        return Decimal('3.59')
    else:
        return Decimal('4.50')


# =========================
# APPLY INTEREST ON APPROVAL
# =========================
def apply_interest_on_approval(loan):

    if loan.loan_type == 'DRIVER' and not loan.interest_rate:
        loan.interest_rate = calculate_driver_interest(loan.amount)
        loan.save(update_fields=['interest_rate'])

    return loan



def calculate_interest(loan):
    return loan.interest_amount()


def calculate_total_amount(loan):
    return loan.total_payable()


def get_total_repaid(loan):
    return loan.total_paid()


def get_balance(loan):
    return loan.balance()


# =========================
# RECORD REPAYMENT

# ── CONCURRENCY FIX ──
# =========================
def record_repayment(loan, amount, source='MANUAL'):
    """
    source can be 'MANUAL', 'MPESA', or 'CREDIT' — for
    bookkeeping/audit purposes if LoanRepayment gains a source
    field later.
    """
    amount = Decimal(amount)

    with transaction.atomic():
        # Lock this loan row until the transaction commits, so a
        # concurrent repayment on the SAME loan must wait and will
        # then see this repayment's effect before making its own
        # PAID/overpayment decision.
        locked_loan = Loan.objects.select_for_update().get(pk=loan.pk)

        LoanRepayment.objects.create(
            loan=locked_loan,
            amount=amount
        )

        if locked_loan.balance() <= 0 and locked_loan.status != 'PAID':
            locked_loan.status = 'PAID'
            locked_loan.save(update_fields=['status'])

    # Refresh the caller's in-memory object so it reflects the
    # committed state (status, related repayments) without
    # requiring the caller to re-fetch from the DB themselves.
    loan.refresh_from_db()
    return loan


# =========================
# LOAN DASHBOARD SUMMARY
# =========================
def get_loan_summary():

    valid_loans = Loan.objects.exclude(status='REJECTED')

    return {
        "active": valid_loans.filter(status='ACTIVE').count(),
        "pending": valid_loans.filter(status='PENDING').count(),
        "paid": valid_loans.filter(status='PAID').count(),

        "bank_loans": valid_loans.filter(loan_type='BANK').count(),
        "driver_loans": valid_loans.filter(loan_type='DRIVER').count(),
    }


# =========================
# FINANCIAL IMPACT (PROFIT TRACKING)
# =========================
def get_loan_financial_impact():

    valid_loans = Loan.objects.exclude(status='REJECTED')

    # NOTE: this expression MUST mirror Loan.interest_amount():
    #   (self.amount * self.interest_rate) / Decimal('100')
    # See test_loan_financial_consistency for the guard against drift.
    interest_expr = ExpressionWrapper(
        (F('amount') * F('interest_rate')) / Decimal('100'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    driver_income = valid_loans.filter(
        loan_type='DRIVER'
    ).aggregate(total=Sum(interest_expr))['total'] or Decimal('0.00')

    bank_cost = valid_loans.filter(
        loan_type='BANK'
    ).aggregate(total=Sum(interest_expr))['total'] or Decimal('0.00')

    return {
        "driver_interest_income": driver_income,
        "bank_interest_expense": bank_cost,
        "net_impact": driver_income - bank_cost
    }