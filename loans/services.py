from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from decimal import Decimal
from .models import Loan, LoanRepayment


# -------------------------
# GET ALL LOANS (ADMIN SAFE VIEW)
# -------------------------
def get_all_loans(loan_type=None, status=None):

    loans = Loan.objects.select_related('driver')

    if status:
        loans = loans.filter(status=status)
    else:
        loans = loans.filter(
            status__in=['REQUESTED', 'PENDING', 'ACTIVE', 'PAID', 'REJECTED']
        )

    if loan_type:
        loans = loans.filter(loan_type=loan_type)

    return loans.order_by('-issued_date')


# -------------------------
# DRIVER LOANS
# -------------------------
def get_driver_loans(driver):

    return Loan.objects.filter(
        driver=driver,
        loan_type='DRIVER'
    ).order_by('-issued_date')


# -------------------------
# BANK LOANS
# -------------------------
def get_bank_loans():

    return Loan.objects.filter(
        loan_type='BANK'
    ).order_by('-issued_date')


# -------------------------
# SINGLE LOAN
# -------------------------
def get_loan(loan_id):

    return Loan.objects.select_related('driver').get(id=loan_id)


# -------------------------
# DRIVER INTEREST RULE ENGINE
# -------------------------
def calculate_driver_interest(amount):

    amount = Decimal(amount)

    if amount <= 100:
        return Decimal('25')
    elif amount <= 1000:
        return Decimal('50')
    elif amount <= 10000:
        return Decimal('25')
    else:
        return Decimal('50')


# -------------------------
# 🔥 APPLY INTEREST (FIXED & GUARANTEED)
# -------------------------
def apply_interest_on_approval(loan):
    """
    Ensures interest is ALWAYS applied when admin approves
    """

    if loan.loan_type == 'DRIVER':

        # prevent overwriting if already set
        if not loan.interest_rate or loan.interest_rate == 0:
            loan.interest_rate = calculate_driver_interest(loan.amount)
            loan.save(update_fields=['interest_rate'])

    return loan


# -------------------------
# INTEREST CALCULATION
# -------------------------
def calculate_interest(loan):

    return (loan.amount * loan.interest_rate) / Decimal('100')


# -------------------------
# TOTAL PAYABLE
# -------------------------
def calculate_total_amount(loan):

    return loan.amount + calculate_interest(loan)


# -------------------------
# TOTAL REPAYED
# -------------------------
def get_total_repaid(loan):

    return loan.repayments.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')


# -------------------------
# BALANCE
# -------------------------
def get_balance(loan):

    return calculate_total_amount(loan) - get_total_repaid(loan)


# -------------------------
# 🔥 RECORD REPAYMENT (MPESA READY)
# -------------------------
def record_repayment(loan, amount, method="MANUAL", reference=None):

    amount = Decimal(str(amount))

    LoanRepayment.objects.create(
        loan=loan,
        amount=amount
        # future fields if added:
        # method=method,
        # reference=reference
    )

    # auto close loan
    if get_balance(loan) <= 0:
        loan.status = 'PAID'
        loan.save(update_fields=['status'])

    return loan


# -------------------------
# PROFIT ENGINE (ACCURATE)
# -------------------------
def get_loan_financial_impact():

    interest_expr = ExpressionWrapper(
        (F('amount') * F('interest_rate')) / Decimal('100'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    driver_interest_income = Loan.objects.filter(
        loan_type='DRIVER'
    ).aggregate(total=Sum(interest_expr))['total'] or Decimal('0.00')

    bank_interest_expense = Loan.objects.filter(
        loan_type='BANK'
    ).aggregate(total=Sum(interest_expr))['total'] or Decimal('0.00')

    return {
        "driver_interest_income": driver_interest_income,
        "bank_interest_expense": bank_interest_expense,
        "net_loan_impact": driver_interest_income - bank_interest_expense
    }


# -------------------------
# LOAN SUMMARY (DASHBOARD READY)
# -------------------------
def get_loan_summary():

    return {
        "active": Loan.objects.filter(status='ACTIVE').count(),
        "pending": Loan.objects.filter(status__in=['PENDING', 'REQUESTED']).count(),
        "paid": Loan.objects.filter(status='PAID').count(),

        "bank_loans": Loan.objects.filter(loan_type='BANK').count(),
        "driver_loans": Loan.objects.filter(loan_type='DRIVER').count(),
    }