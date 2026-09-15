import pytest

from .factories import AccountFactory


@pytest.mark.django_db
class TestAccountModel:
    def test_str_includes_name_and_currency(self):
        account = AccountFactory(name="Main bank", currency="USD")

        assert str(account) == "Main bank (USD)"

    def test_defaults_to_active(self):
        account = AccountFactory()

        assert account.is_active is True
