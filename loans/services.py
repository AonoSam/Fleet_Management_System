from django.db.models import Sum
from decimal import Decimal
from .models import Loan, LoanRepayment


# -------------------------
# GET ALL LOANS
# -------------------------
def get_all_loans(loan_type=None, status=None):

    loans = Loan.objects.select_related('driver')

    if loan_type:
        loans = loans.filter(loan_type=loan_type)

    if status:
        loans = loans.filter(status=status)

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
# BANK LOANS (COMPANY LIABILITY VIEW ONLY)
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
# UPDATE STATUS
# -------------------------
def update_loan_status(loan, status):

    loan.status = status
    loan.save()
    return loan


# -------------------------
# INTEREST CALCULATION (FINANCE CORE)
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
# BALANCE (CASH OUTSTANDING ONLY)
# -------------------------
def get_balance(loan):

    return calculate_total_amount(loan) - get_total_repaid(loan)


# -------------------------
# RECORD REPAYMENT
# -------------------------
def record_repayment(loan, amount):

    amount = Decimal(str(amount))

    LoanRepayment.objects.create(
        loan=loan,
        amount=amount
    )

    if get_balance(loan) <= 0:
        loan.status = 'PAID'
        loan.save()

    return loan


# -------------------------
# 🔥 PROFIT ENGINE (MOST IMPORTANT FIX)
# -------------------------
def get_loan_financial_impact():

    driver_interest_income = Loan.objects.filter(
        loan_type='DRIVER'
    ).aggregate(
        total=Sum((F('amount') * F('interest_rate')) / 100)
    )['total'] or Decimal('0.00')

    bank_interest_expense = Loan.objects.filter(
        loan_type='BANK'
    ).aggregate(
        total=Sum((F('amount') * F('interest_rate')) / 100)
    )['total'] or Decimal('0.00')

    return {
        "driver_interest_income": driver_interest_income,
        "bank_interest_expense": bank_interest_expense,
        "net_loan_impact": driver_interest_income - bank_interest_expense
    }


# -------------------------
# LOAN SUMMARY (REPORTING ONLY)
# -------------------------
def get_loan_summary():

    return {
        "active": Loan.objects.filter(status='ACTIVE').count(),
        "pending": Loan.objects.filter(status='PENDING').count(),
        "paid": Loan.objects.filter(status='PAID').count(),

        "bank_loans": Loan.objects.filter(loan_type='BANK').count(),
        "driver_loans": Loan.objects.filter(loan_type='DRIVER').count(),
    }