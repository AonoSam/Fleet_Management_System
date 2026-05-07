from decimal import Decimal
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from .models import Loan, LoanRepayment


# =========================
# GET ALL LOANS
# =========================
def get_all_loans(loan_type=None, status=None):
    
    loans = Loan.objects.select_related('driver')

    # 🔥 EXCLUDE rejected by default
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
# DRIVER INTEREST RULE ENGINE (FIXED PROPER PERCENTAGE)
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


# =========================
# INTEREST AMOUNT
# =========================
def calculate_interest(loan):

    return (loan.amount * loan.interest_rate) / Decimal('100')


# =========================
# TOTAL PAYABLE
# =========================
def calculate_total_amount(loan):

    return loan.amount + calculate_interest(loan)


# =========================
# TOTAL REPAYED
# =========================
def get_total_repaid(loan):

    return loan.repayments.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')


# =========================
# BALANCE
# =========================
def get_balance(loan):

    return calculate_total_amount(loan) - get_total_repaid(loan)


# =========================
# RECORD REPAYMENT (FIXED)
# =========================
def record_repayment(loan, amount):

    amount = Decimal(amount)

    LoanRepayment.objects.create(
        loan=loan,
        amount=amount
    )

    # update status automatically
    if get_balance(loan) <= 0:
        loan.status = 'PAID'
        loan.save(update_fields=['status'])

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