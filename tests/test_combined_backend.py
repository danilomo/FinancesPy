"""Tests for CombinedBackend implementation."""

import json
from datetime import date

import pytest

from financespy.account import open_account
from financespy.backends.combined_backend import CombinedBackend
from financespy.categories import categories_from_list
from financespy.exceptions import BackendError, DataValidationError
from financespy.money import Money
from financespy.transaction import Transaction


@pytest.fixture
def simple_categories():
    """Simple category structure for testing."""
    return categories_from_list(
        [
            "uncategorized",
            "misc",
            {"food": ["groceries", "restaurant"]},
            {"shopping": ["electronics", "clothing"]},
            "deposit",
            "utilities",
        ]
    )


@pytest.fixture
def test_account_structure(tmp_path, simple_categories):
    """Create test account structure with multiple sub-accounts."""
    # Account 1: girokonto (CSV backend)
    giro_path = tmp_path / "acc1"
    giro_path.mkdir()

    # Create account.json
    with open(giro_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "girokonto",
                "type": "csv",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries", "restaurant"]},
                    {"shopping": ["electronics", "clothing"]},
                    "deposit",
                    "utilities",
                ],
            },
            f,
        )

    # Add some transactions to account 1
    year_path = giro_path / "2023" / "jan"
    year_path.mkdir(parents=True)
    with open(year_path / "15.csv", "w") as f:
        f.write("50.00, Aldi shopping, groceries, food\n")
        f.write("100.00, Salary from Aline, deposit\n")
        f.write("25.00, Lunch at cafe, restaurant\n")

    # Account 2: credit_card (CSV backend)
    card_path = tmp_path / "acc2"
    card_path.mkdir()

    with open(card_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "credit_card",
                "type": "csv",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries", "restaurant"]},
                    {"shopping": ["electronics", "clothing"]},
                    "deposit",
                    "utilities",
                ],
            },
            f,
        )

    # Add some transactions to account 2
    year_path2 = card_path / "2023" / "jan"
    year_path2.mkdir(parents=True)
    with open(year_path2 / "15.csv", "w") as f:
        f.write("200.00, New laptop, electronics, shopping\n")
        f.write("30.00, Dinner, restaurant\n")

    # Combined account
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined_account",
                "type": "combined",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries", "restaurant"]},
                    {"shopping": ["electronics", "clothing"]},
                    "deposit",
                    "utilities",
                ],
                "accounts": [
                    {
                        "name": "girokonto",
                        "path": "../acc1",
                        "exclude": ['is_deposit AND description ~ ".*Aline.*"'],
                    },
                    {"name": "credit_card", "path": "../acc2"},
                ],
            },
            f,
        )

    return {
        "giro_path": str(giro_path),
        "card_path": str(card_path),
        "combined_path": str(combined_path),
        "categories": simple_categories,
    }


# ============================================================================
# Basic Functionality Tests
# ============================================================================


def test_combined_backend_initialization(test_account_structure):
    """Test that CombinedBackend initializes correctly."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    assert account is not None
    assert isinstance(account.backend, CombinedBackend)
    assert len(account.backend._sub_accounts) == 2


def test_query_multiple_accounts(test_account_structure):
    """Test querying transactions from multiple accounts."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    # Query for Jan 15, 2023
    transactions = list(account.records(date(2023, 1, 15)))

    # Should have transactions from both accounts
    # Account 1: groceries (50), deposit (excluded), restaurant (25) = 2 transactions
    # Account 2: electronics (200), restaurant (30) = 2 transactions
    # Total: 4 transactions (deposit is excluded)
    assert len(transactions) == 4

    # Check that transactions have descriptions from both accounts
    descriptions = [t.description for t in transactions]
    assert "Aldi shopping" in descriptions
    assert "New laptop" in descriptions


def test_account_category_tagging(test_account_structure):
    """Test that account name is added as a category to each transaction."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transactions = list(account.records(date(2023, 1, 15)))

    # Find a transaction from girokonto
    giro_trans = [t for t in transactions if t.description == "Aldi shopping"][0]
    category_names = [str(c) for c in giro_trans.categories]
    assert "girokonto" in category_names
    assert "food" in category_names or "groceries" in category_names

    # Find a transaction from credit_card
    card_trans = [t for t in transactions if t.description == "New laptop"][0]
    category_names = [str(c) for c in card_trans.categories]
    assert "credit_card" in category_names


def test_empty_results(test_account_structure):
    """Test handling of dates with no transactions."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    # Query a date with no transactions
    transactions = list(account.records(date(2023, 1, 20)))

    assert len(transactions) == 0


def test_date_queries(test_account_structure):
    """Test that date-based filtering works correctly."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    # Query specific date
    jan_15 = list(account.records(date(2023, 1, 15)))
    jan_16 = list(account.records(date(2023, 1, 16)))

    assert len(jan_15) > 0
    assert len(jan_16) == 0


# ============================================================================
# Exclude Predicate Tests
# ============================================================================


def test_exclude_single_predicate(test_account_structure):
    """Test that exclude predicates filter transactions correctly."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transactions = list(account.records(date(2023, 1, 15)))

    # The deposit transaction with "Aline" should be excluded
    descriptions = [t.description for t in transactions]
    assert "Salary from Aline" not in descriptions

    # Other transactions should be present
    assert "Aldi shopping" in descriptions


def test_exclude_multiple_predicates(tmp_path, simple_categories):
    """Test multiple exclude predicates with AND logic."""
    # Create account with multiple predicates
    giro_path = tmp_path / "acc1"
    giro_path.mkdir()

    with open(giro_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "test_account",
                "type": "csv",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries"]},
                    "deposit",
                ],
            },
            f,
        )

    year_path = giro_path / "2023" / "jan"
    year_path.mkdir(parents=True)
    with open(year_path / "15.csv", "w") as f:
        f.write("50.00, Regular shopping, groceries\n")
        f.write("100.00, Big deposit, deposit\n")
        f.write("10.00, Small purchase, groceries\n")

    # Combined account with multiple exclusions
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries"]},
                    "deposit",
                ],
                "accounts": [
                    {
                        "name": "test_account",
                        "path": "../acc1",
                        "exclude": ["is_deposit", "value < 20.0"],
                    }
                ],
            },
            f,
        )

    account = open_account(str(combined_path))
    transactions = list(account.records(date(2023, 1, 15)))

    # Should only have "Regular shopping" (50.00)
    # Excluded: deposit (is_deposit), Small purchase (value < 20)
    assert len(transactions) == 1
    assert transactions[0].description == "Regular shopping"


def test_exclude_complex_expression(tmp_path, simple_categories):
    """Test complex exclude expressions with category + value filters."""
    giro_path = tmp_path / "acc1"
    giro_path.mkdir()

    with open(giro_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "test_account",
                "type": "csv",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries", "restaurant"]},
                ],
            },
            f,
        )

    year_path = giro_path / "2023" / "jan"
    year_path.mkdir(parents=True)
    with open(year_path / "15.csv", "w") as f:
        f.write("50.00, Aldi, groceries\n")
        f.write("100.00, Big shopping, groceries\n")
        f.write("20.00, Lunch, restaurant\n")

    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": [
                    "uncategorized",
                    "misc",
                    {"food": ["groceries", "restaurant"]},
                ],
                "accounts": [
                    {
                        "name": "test_account",
                        "path": "../acc1",
                        "exclude": ["is_groceries AND (value > 75.0)"],
                    }
                ],
            },
            f,
        )

    account = open_account(str(combined_path))
    transactions = list(account.records(date(2023, 1, 15)))

    # Should exclude "Big shopping" (groceries > 75)
    descriptions = [t.description for t in transactions]
    assert "Aldi" in descriptions
    assert "Lunch" in descriptions
    assert "Big shopping" not in descriptions


def test_exclude_regex_pattern(test_account_structure):
    """Test exclude with regex description matching."""
    # Already tested in the main fixture with ".*Aline.*" pattern
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transactions = list(account.records(date(2023, 1, 15)))
    descriptions = [t.description for t in transactions]

    # Should exclude transactions matching the regex
    assert "Salary from Aline" not in descriptions


def test_invalid_exclude_predicate(tmp_path, simple_categories):
    """Test that invalid exclude predicates raise errors during initialization."""
    giro_path = tmp_path / "acc1"
    giro_path.mkdir()

    with open(giro_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "test_account",
                "type": "csv",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
            },
            f,
        )

    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    # Invalid predicate syntax
    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {
                        "name": "test_account",
                        "path": "../acc1",
                        "exclude": ["invalid syntax here!!!"],
                    }
                ],
            },
            f,
        )

    with pytest.raises(BackendError, match="Invalid exclude predicate"):
        open_account(str(combined_path))


# ============================================================================
# Currency Validation Tests
# ============================================================================


def test_currency_mismatch_error(tmp_path, simple_categories):
    """Test that currency mismatch raises an error."""
    # Account with EUR currency
    acc1_path = tmp_path / "acc1"
    acc1_path.mkdir()

    with open(acc1_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "eur_account",
                "type": "csv",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
            },
            f,
        )

    # Account with USD currency
    acc2_path = tmp_path / "acc2"
    acc2_path.mkdir()

    with open(acc2_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "usd_account",
                "type": "csv",
                "currency": "usd",
                "categories": ["uncategorized", "misc"],
            },
            f,
        )

    # Combined account expecting EUR
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {"name": "eur_account", "path": "../acc1"},
                    {"name": "usd_account", "path": "../acc2"},  # Mismatch!
                ],
            },
            f,
        )

    with pytest.raises(DataValidationError, match="Currency mismatch"):
        open_account(str(combined_path))


def test_consistent_currency_success(test_account_structure):
    """Test that matching currencies work correctly."""
    combined_path = test_account_structure["combined_path"]

    # Should not raise any errors
    account = open_account(combined_path)
    assert account is not None


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_insert_record_raises_error(test_account_structure):
    """Test that insert_record raises error (read-only backend)."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transaction = Transaction(
        value=Money(100.00),
        description="Test transaction",
        categories=[],
    )

    with pytest.raises(BackendError, match="read-only"):
        account.insert_record(date(2023, 1, 15), transaction)


def test_missing_sub_account_path(tmp_path, simple_categories):
    """Test handling of invalid sub-account paths."""
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {
                        "name": "nonexistent",
                        "path": "../nonexistent_account",  # Doesn't exist
                    }
                ],
            },
            f,
        )

    with pytest.raises(BackendError):  # Will raise when sub-account path doesn't exist
        open_account(str(combined_path))


def test_invalid_config_format(tmp_path, simple_categories):
    """Test handling of malformed configuration."""
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    # Missing "accounts" field
    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                # "accounts" field is missing!
            },
            f,
        )

    with pytest.raises(DataValidationError, match="accounts"):
        open_account(str(combined_path))


def test_config_missing_account_name(tmp_path, simple_categories):
    """Test that accounts without names raise errors."""
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {
                        # "name" field is missing!
                        "path": "../acc1"
                    }
                ],
            },
            f,
        )

    with pytest.raises(DataValidationError, match="name"):
        open_account(str(combined_path))


def test_config_missing_account_path(tmp_path, simple_categories):
    """Test that accounts without paths raise errors."""
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {
                        "name": "test_account",
                        # "path" field is missing!
                    }
                ],
            },
            f,
        )

    with pytest.raises(DataValidationError, match="path"):
        open_account(str(combined_path))


# ============================================================================
# Integration Tests
# ============================================================================


def test_open_account_combined(test_account_structure):
    """Test that open_account factory correctly creates combined accounts."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    assert account is not None
    assert isinstance(account.backend, CombinedBackend)
    assert account.metadata.backend_type == "combined"


def test_month_iterator(test_account_structure):
    """Test that month iterator works with combined backend."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    # Get month iterator
    month_iter = account.month(1, 2023)

    # Collect all transactions for the month
    all_transactions = []
    for day in month_iter.days():
        all_transactions.extend(list(day.records()))

    # Should have transactions from both accounts (excluding filtered ones)
    assert len(all_transactions) == 4


def test_filtering_by_account_name(test_account_structure):
    """Test that we can filter by account name category."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transactions = list(account.records(date(2023, 1, 15)))

    # Filter by account name (should work because it's added as a category)
    giro_transactions = [t for t in transactions if t.matches_category("girokonto")]
    card_transactions = [t for t in transactions if t.matches_category("credit_card")]

    assert len(giro_transactions) > 0
    assert len(card_transactions) > 0

    # Verify correct categorization
    assert all("Aline" not in t.description for t in giro_transactions)


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_relative_path_resolution(test_account_structure):
    """Test that relative paths are resolved correctly."""
    # This is already tested implicitly by other tests
    # which use relative paths like "../acc1"
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    # Should successfully open and query
    transactions = list(account.records(date(2023, 1, 15)))
    assert len(transactions) > 0


def test_transaction_id_preservation(test_account_structure):
    """Test that original transaction IDs are preserved."""
    combined_path = test_account_structure["combined_path"]
    account = open_account(combined_path)

    transactions = list(account.records(date(2023, 1, 15)))

    # Note: CSV backend doesn't support IDs, so IDs will be None
    # But cloning should preserve whatever ID exists
    for trans in transactions:
        # ID should be None or a valid string (not corrupted)
        assert trans.id is None or isinstance(trans.id, str)


def test_empty_sub_accounts(tmp_path, simple_categories):
    """Test handling of sub-accounts with no transactions."""
    # Create empty account
    acc1_path = tmp_path / "acc1"
    acc1_path.mkdir()

    with open(acc1_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "empty_account",
                "type": "csv",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
            },
            f,
        )

    # Combined account
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [{"name": "empty_account", "path": "../acc1"}],
            },
            f,
        )

    account = open_account(str(combined_path))

    # Should return empty results without errors
    transactions = list(account.records(date(2023, 1, 15)))
    assert len(transactions) == 0


def test_context_manager_cleanup(test_account_structure):
    """Test that context manager properly cleans up sub-accounts."""
    combined_path = test_account_structure["combined_path"]

    account = open_account(combined_path)
    backend = account.backend

    with backend:
        # Use the backend
        transactions = list(backend.records(date(2023, 1, 15)))
        assert len(transactions) > 0

    # After exiting context, sub_accounts should be cleared
    assert len(backend._sub_accounts) == 0


def test_absolute_path_resolution(tmp_path, simple_categories):
    """Test that absolute paths work correctly."""
    # Create account
    acc1_path = tmp_path / "acc1"
    acc1_path.mkdir()

    with open(acc1_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "test_account",
                "type": "csv",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
            },
            f,
        )

    year_path = acc1_path / "2023" / "jan"
    year_path.mkdir(parents=True)
    with open(year_path / "15.csv", "w") as f:
        f.write("50.00, Test transaction, misc\n")

    # Combined account with ABSOLUTE path
    combined_path = tmp_path / "combined"
    combined_path.mkdir()

    with open(combined_path / "account.json", "w") as f:
        json.dump(
            {
                "name": "combined",
                "type": "combined",
                "currency": "eur",
                "categories": ["uncategorized", "misc"],
                "accounts": [
                    {
                        "name": "test_account",
                        "path": str(acc1_path),  # Absolute path
                    }
                ],
            },
            f,
        )

    account = open_account(str(combined_path))
    transactions = list(account.records(date(2023, 1, 15)))

    assert len(transactions) == 1
    assert transactions[0].description == "Test transaction"
