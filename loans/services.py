from .models import Loan


def get_all_loans():
    return Loan.objects.select_related('driver').all()


def get_driver_loans(driver):
    return Loan.objects.filter(driver=driver).order_by('-issued_date')


def get_loan(loan_id):
    return Loan.objects.select_related('driver').get(id=loan_id)


def update_loan_status(loan, status):
    loan.status = status
    loan.save()
    return loan