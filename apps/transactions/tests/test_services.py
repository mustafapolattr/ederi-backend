from decimal import Decimal

import pytest

from apps.accounts.tests.factories import AccountFactory
from apps.transactions.models import Transaction
from apps.transactions.services import annotate_balances, get_account_balance
from apps.users.tests.factories import UserFactory

from .factories import TransactionFactory


@pytest.mark.django_db
class TestGetAccountBalance:
    def test_starting_balance_with_no_transactions(self):
        account = AccountFactory(initial_balance="1000.00")

        assert get_account_balance(account) == Decimal("1000.00")

    def test_expense_decreases_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        TransactionFactory(account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00")

        assert get_account_balance(account) == Decimal("900.00")

    def test_income_increases_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        TransactionFactory(account=account, type=Transaction.TransactionType.INCOME, amount="250.00")

        assert get_account_balance(account) == Decimal("1250.00")

    def test_refund_increases_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        TransactionFactory(account=account, type=Transaction.TransactionType.REFUND, amount="40.00")

        assert get_account_balance(account) == Decimal("1040.00")

    def test_positive_adjustment_increases_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        TransactionFactory(account=account, type=Transaction.TransactionType.ADJUSTMENT, amount="15.00")

        assert get_account_balance(account) == Decimal("1015.00")

    def test_negative_adjustment_decreases_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        TransactionFactory(account=account, type=Transaction.TransactionType.ADJUSTMENT, amount="-15.00")

        assert get_account_balance(account) == Decimal("985.00")

    def test_transfer_moves_money_between_accounts_and_preserves_net_worth(self):
        user = UserFactory()
        account_a = AccountFactory(user=user, initial_balance="1000.00", currency="USD")
        account_b = AccountFactory(user=user, initial_balance="500.00", currency="USD")
        net_worth_before = get_account_balance(account_a) + get_account_balance(account_b)

        TransactionFactory(
            user=user,
            account=account_a,
            to_account=account_b,
            type=Transaction.TransactionType.TRANSFER,
            amount="200.00",
            currency="USD",
        )

        assert get_account_balance(account_a) == Decimal("800.00")
        assert get_account_balance(account_b) == Decimal("700.00")
        net_worth_after = get_account_balance(account_a) + get_account_balance(account_b)
        assert net_worth_after == net_worth_before

    def test_deleting_a_transaction_reverses_its_effect(self):
        account = AccountFactory(initial_balance="1000.00")
        transaction = TransactionFactory(account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00")
        assert get_account_balance(account) == Decimal("900.00")

        transaction.delete()

        assert get_account_balance(account) == Decimal("1000.00")

    def test_editing_a_transaction_amount_changes_balance(self):
        account = AccountFactory(initial_balance="1000.00")
        transaction = TransactionFactory(account=account, type=Transaction.TransactionType.EXPENSE, amount="100.00")

        transaction.amount = Decimal("300.00")
        transaction.save(update_fields=["amount"])

        assert get_account_balance(account) == Decimal("700.00")


@pytest.mark.django_db
class TestAnnotateBalances:
    def test_matches_get_account_balance_for_multiple_accounts(self):
        user = UserFactory()
        account_a = AccountFactory(user=user, initial_balance="1000.00", currency="USD")
        account_b = AccountFactory(user=user, initial_balance="500.00", currency="USD")
        TransactionFactory(account=account_a, user=user, type=Transaction.TransactionType.EXPENSE, amount="100.00")
        TransactionFactory(
            account=account_a,
            to_account=account_b,
            user=user,
            type=Transaction.TransactionType.TRANSFER,
            amount="200.00",
            currency="USD",
        )

        from apps.accounts.models import Account

        annotated = {
            a.id: a.current_balance for a in annotate_balances(Account.objects.filter(user=user))
        }

        assert annotated[account_a.id] == get_account_balance(account_a)
        assert annotated[account_b.id] == get_account_balance(account_b)
