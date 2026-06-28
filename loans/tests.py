"""
loans/tests.py

This test suite exists specifically to catch the class of bug
identified in the production incident review: silent numerical
drift between Loan model methods and the services.py aggregate
queries that reimplement the same math in raw SQL for
performance reasons.

If this test ever fails, it means someone changed
Loan.interest_amount() (or related model math) without updating
the matching SQL expression in get_loan_financial_impact() —
exactly the scenario that would otherwise ship a silently wrong
finance dashboard to production.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Loan, LoanRepayment
from .services import (
    get_loan_financial_impact,
    record_repayment,
    get_balance,
    calculate_total_amount,
    get_total_repaid,
)

User = get_user_model()


class LoanFinancialConsistencyTests(TestCase):
    """
    Guards against services.py duplicating Loan model math and
    drifting out of sync.
    """

    def setUp(self):
        self.driver = User.objects.create_user(
            username='test_driver',
            password='testpass123',
            role='DRIVER'
        )

    def test_services_wrappers_match_model_methods(self):
        """
        calculate_total_amount/get_total_repaid/get_balance must
        return EXACTLY what the model's own methods return — they
        are thin wrappers, not separate implementations.
        """
        loan = Loan.objects.create(
            loan_type='DRIVER',
            driver=self.driver,
            amount=Decimal('5000.00'),
            interest_rate=Decimal('2.76'),
            status='ACTIVE',
        )

        self.assertEqual(calculate_total_amount(loan), loan.total_payable())
        self.assertEqual(get_total_repaid(loan), loan.total_paid())
        self.assertEqual(get_balance(loan), loan.balance())

        record_repayment(loan, Decimal('1000.00'))
        loan.refresh_from_db()

        # After a repayment, wrappers must still agree with the model
        self.assertEqual(get_total_repaid(loan), loan.total_paid())
        self.assertEqual(get_balance(loan), loan.balance())

    def test_financial_impact_matches_model_interest_amount(self):
        """
        THE CRITICAL TEST: get_loan_financial_impact()'s SQL-level
        interest sum must equal manually summing
        loan.interest_amount() in Python for the same loans.

        If someone changes the interest formula on the model
        without updating the SQL expression, this test fails.
        """
        driver_loan = Loan.objects.create(
            loan_type='DRIVER',
            driver=self.driver,
            amount=Decimal('10000.00'),
            interest_rate=Decimal('3.01'),
            status='ACTIVE',
        )

        bank_loan = Loan.objects.create(
            loan_type='BANK',
            driver=None,
            amount=Decimal('500000.00'),
            interest_rate=Decimal('12.00'),
            status='ACTIVE',
        )

        # Ground truth: sum the model's own interest_amount() in Python
        expected_driver_income = driver_loan.interest_amount()
        expected_bank_cost = bank_loan.interest_amount()

        impact = get_loan_financial_impact()

        self.assertEqual(
            impact['driver_interest_income'],
            expected_driver_income,
            "Dashboard driver interest income has DRIFTED from "
            "Loan.interest_amount() — the SQL expression in "
            "get_loan_financial_impact() no longer matches the model."
        )

        self.assertEqual(
            impact['bank_interest_expense'],
            expected_bank_cost,
            "Dashboard bank interest expense has DRIFTED from "
            "Loan.interest_amount() — the SQL expression in "
            "get_loan_financial_impact() no longer matches the model."
        )

    def test_record_repayment_marks_loan_paid_at_zero_balance(self):
        loan = Loan.objects.create(
            loan_type='DRIVER',
            driver=self.driver,
            amount=Decimal('1000.00'),
            interest_rate=Decimal('1.00'),
            status='ACTIVE',
        )

        total_payable = loan.total_payable()
        record_repayment(loan, total_payable)
        loan.refresh_from_db()

        self.assertEqual(loan.status, 'PAID')
        self.assertLessEqual(loan.balance(), Decimal('0.00'))

    def test_record_repayment_does_not_mark_paid_early(self):
        loan = Loan.objects.create(
            loan_type='DRIVER',
            driver=self.driver,
            amount=Decimal('1000.00'),
            interest_rate=Decimal('1.00'),
            status='ACTIVE',
        )

        record_repayment(loan, Decimal('100.00'))
        loan.refresh_from_db()

        self.assertNotEqual(loan.status, 'PAID')
        self.assertGreater(loan.balance(), Decimal('0.00'))