import json
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import financespy.account as acc
from financespy.backends.memory_backend import MemoryBackend
from financespy.backends.sql_backend import (
    Account,
    Base,
    SQLBackend,
    Transaction,
    read_account_metadata,
)
from financespy.money import Money
from financespy.transaction import Transaction as DomainTransaction
from financespy.transaction import parse_transaction

from .test_utils import parse_date


@pytest.fixture
def records(categories):
    RECORDS = """2019-09-04;20.0, withdrawal
    2019-09-05;20.58, rewe
    2019-09-06;49.28, aldi
    2019-09-08;17.05, müller
    2019-09-08;97.2, monthly_ticket
    2019-09-11;50.0, withdrawal
    2019-09-13;50.0, lidl
    2019-09-19;40.0, h_&_m
    2019-09-20;55.58, lidl
    2019-09-21;50.0, withdrawal
    2019-09-21;25.0, train_ticket"""
    recs = (tuple(line.split(";")) for line in RECORDS.split("\n"))
    return [
        (parse_date(date.strip()), parse_transaction(trans, categories))
        for date, trans in recs
    ]


@pytest.fixture
def account(category_list, categories):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    test_account = Account(
        name="savings",
        currency="eur",
        categories=json.dumps(category_list),
        user_id=1,
        created_at=parse_date("2023-01-01"),
    )
    session.add(test_account)
    session.commit()
    account_data = read_account_metadata(session, 1)
    backend = SQLBackend(
        account_id=1,
        session=session,
        categories=categories,
    )

    if account_data is None:
        raise ValueError("Failed to read account metadata")
    return acc.Account(backend, account_data)


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks


def test_month_iterator(account, records):
    backend = account.backend

    cats = backend.categories
    memory_backend = MemoryBackend(cats)

    for dt, rec in records:
        backend.insert_record(dt, rec)
        memory_backend.insert_record(dt, rec)

    weeks1 = backend.month("sep", 2019).weeks()
    weeks2 = memory_backend.month("sep", 2019).weeks()

    assert total_iterator(weeks1) == total_iterator(weeks2)

    month1 = backend.month("sep", 2019).days()
    month2 = memory_backend.month("sep", 2019).days()

    assert total_iterator(month1) == total_iterator(month2)


class TestCategoryMembershipStorage:
    """Tests for JSON category membership storage."""

    @pytest.fixture
    def sql_backend(self, categories):
        """Create a fresh SQL backend for each test."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()

        test_account = Account(
            name="test",
            currency="eur",
            categories="[]",
            user_id=1,
            created_at=date(2023, 1, 1),
        )
        session.add(test_account)
        session.commit()

        return SQLBackend(account_id=1, session=session, categories=categories)

    def test_category_membership_stored_on_insert(self, sql_backend, categories):
        """Test that category_membership JSON is stored with ancestors."""
        lidl = categories.category("lidl")
        transaction = DomainTransaction(
            value=Money(cents=1000),
            categories=[lidl],
            description="test purchase",
        )

        sql_backend.insert_record(date(2024, 1, 15), transaction)

        # Query the raw database to check category_membership
        db_trans = sql_backend.session.query(Transaction).first()
        assert db_trans is not None
        assert db_trans.category_membership is not None

        # Should contain lidl and all its ancestors
        membership = db_trans.category_membership
        assert membership.get("lidl") is True
        assert membership.get("groceries") is True
        assert membership.get("food") is True
        assert membership.get("expenses") is True

    def test_category_membership_multiple_categories(self, sql_backend, categories):
        """Test category_membership with multiple categories."""
        lidl = categories.category("lidl")
        restaurant = categories.category("restaurant")
        transaction = DomainTransaction(
            value=Money(cents=2000),
            categories=[lidl, restaurant],
            description="mixed purchase",
        )

        sql_backend.insert_record(date(2024, 1, 15), transaction)

        db_trans = sql_backend.session.query(Transaction).first()
        membership = db_trans.category_membership

        # Both category hierarchies should be present
        assert membership.get("lidl") is True
        assert membership.get("groceries") is True
        assert membership.get("restaurant") is True
        assert membership.get("food") is True  # Common ancestor


class TestQueryWithPredicate:
    """Tests for the query_with_predicate method."""

    @pytest.fixture
    def populated_backend(self, categories):
        """Create a SQL backend with test data."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()

        test_account = Account(
            name="test",
            currency="eur",
            categories="[]",
            user_id=1,
            created_at=date(2023, 1, 1),
        )
        session.add(test_account)
        session.commit()

        backend = SQLBackend(account_id=1, session=session, categories=categories)

        # Insert test transactions
        test_data = [
            (date(2024, 1, 10), "lidl", 1500, "weekly groceries"),
            (date(2024, 1, 12), "aldi", 2000, "big shopping"),
            (date(2024, 1, 15), "restaurant", 3500, "dinner out"),
            (date(2024, 1, 20), "rewe", 800, "quick stop"),
            (date(2024, 2, 5), "edeka", 2200, "february groceries"),
            (date(2024, 2, 10), "kfc", 1200, "fast food"),
        ]

        for dt, cat_name, cents, desc in test_data:
            cat = categories.category(cat_name)
            transaction = DomainTransaction(
                value=Money(cents=cents),
                categories=[cat],
                description=desc,
            )
            backend.insert_record(dt, transaction)

        return backend

    def test_query_single_category(self, populated_backend):
        """Test querying for a single category."""
        results = list(
            populated_backend.query_with_predicate("is_lidl", dialect="sqlite")
        )
        assert len(results) == 1
        assert results[0].description == "weekly groceries"

    def test_query_parent_category(self, populated_backend):
        """Test querying for a parent category matches children."""
        results = list(
            populated_backend.query_with_predicate("is_groceries", dialect="sqlite")
        )
        # Should match: lidl, aldi, rewe, edeka
        assert len(results) == 4
        descriptions = {r.description for r in results}
        assert "weekly groceries" in descriptions
        assert "big shopping" in descriptions
        assert "quick stop" in descriptions
        assert "february groceries" in descriptions

    def test_query_with_not(self, populated_backend):
        """Test querying with NOT operator."""
        results = list(
            populated_backend.query_with_predicate(
                "is_food AND (NOT is_groceries)", dialect="sqlite"
            )
        )
        # Should match: restaurant, kfc (food but not groceries)
        assert len(results) == 2
        descriptions = {r.description for r in results}
        assert "dinner out" in descriptions
        assert "fast food" in descriptions

    def test_query_with_date_range(self, populated_backend):
        """Test querying with date filters."""
        results = list(
            populated_backend.query_with_predicate(
                "is_groceries",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                dialect="sqlite",
            )
        )
        # Should only get January groceries: lidl, aldi, rewe
        assert len(results) == 3

    def test_query_with_value_comparison(self, populated_backend):
        """Test querying with value comparison."""
        results = list(
            populated_backend.query_with_predicate(
                "is_food AND (value > 2000)", dialect="sqlite"
            )
        )
        # Should match: aldi (2000), restaurant (3500), edeka (2200)
        # Note: value > 2000, not >=, so aldi might not match
        assert len(results) >= 2
        for r in results:
            assert r.value.cents() > 2000

    def test_query_or_categories(self, populated_backend):
        """Test querying with OR operator."""
        results = list(
            populated_backend.query_with_predicate(
                "is_lidl OR is_restaurant", dialect="sqlite"
            )
        )
        assert len(results) == 2
        descriptions = {r.description for r in results}
        assert "weekly groceries" in descriptions
        assert "dinner out" in descriptions
