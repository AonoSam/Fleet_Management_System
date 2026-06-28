from django.db.models import Sum
from payments.models import Payment
from maintainance.models import RepairLog
from accounts.models import User
from loans.models import Loan


# ----------------------
# DASHBOARD STATS (REAL ACCOUNTING ENGINE)
# ----------------------
def get_dashboard_stats():

    # ---------------- INCOME ----------------
    payment_income = Payment.objects.filter(
        status='SUCCESS'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ✅ ONLY VALID DRIVER LOANS
    driver_loans = Loan.objects.filter(
        loan_type='DRIVER',
        status__in=['ACTIVE', 'PAID']
    )

    driver_interest_income = sum(
        loan.interest_income() for loan in driver_loans
    )

    total_income = payment_income + driver_interest_income


    # ---------------- EXPENSES ----------------
    maintenance_expenses = RepairLog.objects.aggregate(
        total=Sum('cost')
    )['total'] or 0

    # ✅ ONLY VALID BANK LOANS
    bank_loans = Loan.objects.filter(
        loan_type='BANK',
        status__in=['ACTIVE', 'PAID']
    )

    bank_interest_expense = sum(
        loan.interest_expense() for loan in bank_loans
    )

    total_expenses = maintenance_expenses + bank_interest_expense


    # ---------------- LOAN KPI (FIXED) ----------------
    valid_loans = Loan.objects.filter(
        status__in=['ACTIVE', 'PAID']
    )

    total_loan_amount = valid_loans.aggregate(
        total=Sum('amount')
    )['total'] or 0

    active_loans = Loan.objects.filter(status='ACTIVE').count()

    # 🔥 FIX: pending should NOT include rejected
    pending_loans = Loan.objects.filter(
        status__in=['PENDING', 'REQUESTED']
    ).count()

    paid_loans = Loan.objects.filter(status='PAID').count()


    # ---------------- FINAL PROFIT ----------------
    net_profit = total_income - total_expenses


    return {
        "total_income": total_income,
        "total_expenses": total_expenses,

        "driver_interest_income": driver_interest_income,
        "bank_interest_expense": bank_interest_expense,

        "total_loan_amount": total_loan_amount,
        "active_loans": active_loans,
        "pending_loans": pending_loans,
        "paid_loans": paid_loans,

        "net_profit": net_profit,
        "total_drivers": User.objects.filter(role='DRIVER').count(),
    }


# ----------------------
# COST REPORT
# ----------------------
def get_cost_report():
    return RepairLog.objects.select_related('vehicle').order_by('-repaired_on')


# ----------------------
# DRIVER PERFORMANCE REPORT (FIXED)
# ----------------------
def get_driver_performance_report():

    drivers = User.objects.filter(role='DRIVER')

    report = []

    for d in drivers:

        payments = Payment.objects.filter(driver=d, status='SUCCESS')

        # ✅ ONLY VALID LOANS
        loans = Loan.objects.filter(
            driver=d,
            loan_type='DRIVER',
            status__in=['ACTIVE', 'PAID']
        )

        income = payments.aggregate(total=Sum('amount'))['total'] or 0
        loan_amount = loans.aggregate(total=Sum('amount'))['total'] or 0
        trips = payments.count()

        # ✅ Balanced scoring
        score = (float(income) * 0.7) - (float(loan_amount) * 0.2) + (trips * 10)

        report.append({
            "driver": d,
            "total_income": income,
            "total_loans": loan_amount,
            "trips": trips,
            "score": round(score, 2)
        })

    return report