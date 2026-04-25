from .models import Loan, LoanRepayment


def get_loans():
    return Loan.objects.all().order_by('-loan_date')


def create_loan(data):
    return Loan.objects.create(**data)


def get_loan(loan_id):
    return Loan.objects.get(id=loan_id)


def add_repayment(loan, amount):
    repayment = LoanRepayment.objects.create(
        loan=loan,
        amount_paid=amount
    )

    # update loan status
    total_paid = sum(r.amount_paid for r in loan.repayments.all())

    if total_paid >= loan.amount:
        loan.is_paid = True
        loan.save()

    return repayment