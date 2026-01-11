"""Tests for predicate compiler module."""

from datetime import date

import pytest

from financespy.categories import categories_from_list
from financespy.money import Money
from financespy.predicate_compiler import (
    PredicateCompilationError,
    PredicateCompiler,
    compile_predicate,
)
from financespy.transaction import Transaction


@pytest.fixture
def categories():
    """Create a category hierarchy for testing."""
    return categories_from_list(
        [
            {
                "expenses": [
                    {"others": ["uncategorized"]},
                    {
                        "food": [
                            {"groceries": ["aldi", "kaufland", "edeka"]},
                            "restaurant",
                        ]
                    },
                    {"shopping": ["electronics", "clothing"]},
                    "utilities",
                ]
            }
        ]
    )


@pytest.fixture
def groceries_transaction(categories):
    """Create a groceries transaction."""
    return Transaction(
        value=Money(cents=2550),  # 25.50
        description="Weekly shopping",
        categories=[categories.category("aldi")],
        date=date(2025, 1, 15),
    )


@pytest.fixture
def restaurant_transaction(categories):
    """Create a restaurant transaction."""
    return Transaction(
        value=Money(cents=4500),  # 45.00
        description="Dinner with friends",
        categories=[categories.category("restaurant")],
        date=date(2025, 2, 10),
    )


@pytest.fixture
def kaufland_transaction(categories):
    """Create a kaufland transaction."""
    return Transaction(
        value=Money(cents=1200),  # 12.00
        description="Quick shopping at kaufland",
        categories=[categories.category("kaufland")],
        date=date(2025, 1, 20),
    )


class TestCategoryPredicates:
    """Test category-based predicates."""

    def test_simple_category_check(self, groceries_transaction):
        """Test simple is_category predicate."""
        pred = compile_predicate("is_groceries")
        assert pred(groceries_transaction)

    def test_specific_store_check(self, groceries_transaction):
        """Test specific store category."""
        pred = compile_predicate("is_aldi")
        assert pred(groceries_transaction)

    def test_hierarchical_category(self, groceries_transaction):
        """Test hierarchical category matching."""
        pred = compile_predicate("is_food")
        assert pred(groceries_transaction)

    def test_category_not_match(self, groceries_transaction):
        """Test category that doesn't match."""
        pred = compile_predicate("is_restaurant")
        assert not pred(groceries_transaction)


class TestBooleanOperators:
    """Test boolean operators (AND, OR, NOT)."""

    def test_and_operator_both_true(self, groceries_transaction):
        """Test AND with both conditions true."""
        pred = compile_predicate("is_groceries AND is_food")
        assert pred(groceries_transaction)

    def test_and_operator_one_false(self, groceries_transaction):
        """Test AND with one condition false."""
        pred = compile_predicate("is_groceries AND is_restaurant")
        assert not pred(groceries_transaction)

    def test_or_operator_one_true(self, groceries_transaction):
        """Test OR with one condition true."""
        pred = compile_predicate("is_groceries OR is_restaurant")
        assert pred(groceries_transaction)

    def test_or_operator_both_false(self, groceries_transaction):
        """Test OR with both conditions false."""
        pred = compile_predicate("is_restaurant OR is_utilities")
        assert not pred(groceries_transaction)

    def test_not_operator(self, groceries_transaction):
        """Test NOT operator."""
        pred = compile_predicate("NOT is_restaurant")
        assert pred(groceries_transaction)

    def test_not_with_true_condition(self, groceries_transaction):
        """Test NOT with true condition."""
        pred = compile_predicate("NOT is_groceries")
        assert not pred(groceries_transaction)

    def test_complex_boolean_expression(
        self, groceries_transaction, kaufland_transaction
    ):
        """Test complex boolean expression from requirements."""
        pred = compile_predicate("is_groceries AND (NOT is_kaufland)")

        # aldi transaction should match
        assert pred(groceries_transaction)

        # kaufland transaction should not match
        assert not pred(kaufland_transaction)

    def test_parentheses_grouping(self, groceries_transaction):
        """Test parentheses for grouping."""
        pred = compile_predicate("(is_groceries OR is_restaurant) AND is_food")
        assert pred(groceries_transaction)


class TestValueComparisons:
    """Test value-based comparisons."""

    def test_value_greater_than(self, groceries_transaction):
        """Test value > comparison."""
        pred = compile_predicate("value > 20.0")
        assert pred(groceries_transaction)  # 25.50 > 20.0

    def test_value_less_than(self, groceries_transaction):
        """Test value < comparison."""
        pred = compile_predicate("value < 30.0")
        assert pred(groceries_transaction)  # 25.50 < 30.0

    def test_value_equal(self, groceries_transaction):
        """Test value == comparison."""
        pred = compile_predicate("value == 25.50")
        assert pred(groceries_transaction)

    def test_value_greater_equal(self, restaurant_transaction):
        """Test value >= comparison."""
        pred = compile_predicate("value >= 45.0")
        assert pred(restaurant_transaction)

    def test_value_less_equal(self, restaurant_transaction):
        """Test value <= comparison."""
        pred = compile_predicate("value <= 45.0")
        assert pred(restaurant_transaction)

    def test_value_not_equal(self, groceries_transaction):
        """Test value != comparison."""
        pred = compile_predicate("value != 30.0")
        assert pred(groceries_transaction)

    def test_combined_category_and_value(
        self, groceries_transaction, restaurant_transaction
    ):
        """Test combining category check with value comparison."""
        pred = compile_predicate("is_groceries AND (value > 10.0)")

        assert pred(groceries_transaction)  # groceries and value > 10
        assert not pred(restaurant_transaction)  # not groceries


class TestDateComparisons:
    """Test date-based comparisons."""

    def test_date_greater_than(self, groceries_transaction):
        """Test date > comparison."""
        pred = compile_predicate('date > "10/01/2025"')
        assert pred(groceries_transaction)  # 2025-01-15 > 2025-01-10

    def test_date_less_than(self, groceries_transaction):
        """Test date < comparison."""
        pred = compile_predicate('date < "20/01/2025"')
        assert pred(groceries_transaction)  # 2025-01-15 < 2025-01-20

    def test_date_equal(self, groceries_transaction):
        """Test date == comparison."""
        pred = compile_predicate('date == "15/01/2025"')
        assert pred(groceries_transaction)

    def test_date_range(self, groceries_transaction, restaurant_transaction):
        """Test date range from requirements."""
        pred = compile_predicate('"20/01/2025" > date AND date >= "10/01/2025"')

        assert pred(groceries_transaction)  # 2025-01-15 in range
        assert not pred(restaurant_transaction)  # 2025-02-10 not in range

    def test_date_format_iso(self, groceries_transaction):
        """Test ISO date format (YYYY-MM-DD)."""
        pred = compile_predicate('date == "2025-01-15"')
        assert pred(groceries_transaction)

    def test_combined_category_date_value(
        self, restaurant_transaction, kaufland_transaction
    ):
        """Test complex predicate from requirements."""
        # Note: Changed expression to match intent (date after 20/01/2025)
        pred = compile_predicate(
            'is_restaurant AND (date > "20/01/2025" AND date <= "20/02/2025")'
        )

        # Restaurant transaction on 2025-02-10 should match
        assert pred(restaurant_transaction)

        # Kaufland on 2025-01-20 is in date range but not restaurant
        assert not pred(kaufland_transaction)


class TestDescriptionPredicates:
    """Test description-based predicates."""

    def test_description_equality(self, groceries_transaction):
        """Test description == comparison."""
        pred = compile_predicate('description == "Weekly shopping"')
        assert pred(groceries_transaction)

    def test_description_not_equal(self, groceries_transaction):
        """Test description != comparison."""
        pred = compile_predicate('description != "Other text"')
        assert pred(groceries_transaction)

    def test_description_regex_match(self, kaufland_transaction):
        """Test description ~ regex matching."""
        pred = compile_predicate('description ~ ".*kaufland.*"')
        assert pred(kaufland_transaction)

    def test_description_regex_case_sensitive(self, kaufland_transaction):
        """Test regex is case-sensitive by default."""
        pred = compile_predicate('description ~ ".*KAUFLAND.*"')
        assert not pred(kaufland_transaction)

    def test_description_regex_complex(self, groceries_transaction):
        """Test complex regex pattern."""
        pred = compile_predicate('description ~ "^Weekly.*"')
        assert pred(groceries_transaction)

    def test_description_regex_no_match(self, groceries_transaction):
        """Test regex that doesn't match."""
        pred = compile_predicate('description ~ ".*dinner.*"')
        assert not pred(groceries_transaction)


class TestComplexPredicates:
    """Test complex predicate combinations."""

    def test_all_operators_combined(self, groceries_transaction):
        """Test combining all operator types."""
        pred = compile_predicate(
            "is_groceries AND (value > 20.0) AND "
            '(date >= "01/01/2025") AND '
            '(description ~ ".*shopping.*")'
        )
        assert pred(groceries_transaction)

    def test_nested_boolean_logic(self, groceries_transaction):
        """Test nested boolean expressions."""
        pred = compile_predicate(
            "(is_groceries OR is_restaurant) AND "
            "((value > 10.0 AND value < 30.0) OR "
            '(description ~ ".*special.*"))'
        )
        assert pred(groceries_transaction)

    def test_multiple_not_operators(self, groceries_transaction):
        """Test multiple NOT operators."""
        pred = compile_predicate(
            "is_groceries AND (NOT is_restaurant) AND (NOT is_utilities)"
        )
        assert pred(groceries_transaction)


class TestErrorHandling:
    """Test error handling and validation."""

    def test_empty_expression(self):
        """Test empty expression raises error."""
        with pytest.raises(PredicateCompilationError):
            compile_predicate("")

    def test_invalid_syntax(self):
        """Test invalid syntax raises error."""
        with pytest.raises(PredicateCompilationError):
            compile_predicate("is_groceries AND AND is_food")

    def test_invalid_regex_pattern(self):
        """Test invalid regex pattern raises error."""
        with pytest.raises(PredicateCompilationError):
            compile_predicate('description ~ "[invalid"')

    def test_invalid_date_format(self):
        """Test invalid date format raises error."""
        with pytest.raises(PredicateCompilationError):
            pred = compile_predicate('date > "invalid-date"')
            # Error occurs during evaluation
            transaction = Transaction(
                value=Money(cents=1000),
                description="test",
                categories=[],
                date=date(2025, 1, 1),
            )
            pred(transaction)

    def test_unsupported_operator(self):
        """Test unsupported operator raises error."""
        with pytest.raises(PredicateCompilationError):
            compile_predicate("value ** 2 > 100")

    def test_chained_comparison_not_supported(self):
        """Test chained comparisons are not supported."""
        with pytest.raises(PredicateCompilationError):
            compile_predicate("10 < value < 20")


class TestPredicateCompilerClass:
    """Test PredicateCompiler class directly."""

    def test_compiler_reuse(self, groceries_transaction):
        """Test compiler can be reused for multiple expressions."""
        compiler = PredicateCompiler()

        pred1 = compiler.compile("is_groceries")
        pred2 = compiler.compile("value > 20.0")

        assert pred1(groceries_transaction)
        assert pred2(groceries_transaction)

    def test_compiler_independence(self, groceries_transaction):
        """Test predicates are independent."""
        compiler = PredicateCompiler()

        pred1 = compiler.compile("is_groceries")
        pred2 = compiler.compile("is_restaurant")

        # Both predicates should work independently
        assert pred1(groceries_transaction)
        assert not pred2(groceries_transaction)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_transaction_without_date(self, categories):
        """Test predicate on transaction without date."""
        transaction = Transaction(
            value=Money(cents=1000),
            description="test",
            categories=[categories.category("groceries")],
            date=None,
        )

        # Category predicate should still work
        pred = compile_predicate("is_groceries")
        assert pred(transaction)

    def test_transaction_empty_description(self, categories):
        """Test predicate on transaction with empty description."""
        transaction = Transaction(
            value=Money(cents=1000),
            description="",
            categories=[categories.category("groceries")],
            date=date(2025, 1, 1),
        )

        pred = compile_predicate('description == ""')
        assert pred(transaction)

    def test_zero_value_comparison(self, categories):
        """Test comparison with zero value."""
        transaction = Transaction(
            value=Money(cents=0),
            description="test",
            categories=[categories.category("groceries")],
        )

        pred = compile_predicate("value == 0.0")
        assert pred(transaction)

    def test_negative_value(self, categories):
        """Test negative value comparison."""
        transaction = Transaction(
            value=Money(cents=-1000),  # -10.00
            description="refund",
            categories=[categories.category("groceries")],
        )

        pred = compile_predicate("value < 0")
        assert pred(transaction)


class TestRealWorldExamples:
    """Test real-world usage examples."""

    def test_filter_expensive_groceries(self, categories):
        """Test filtering expensive grocery transactions."""
        transactions = [
            Transaction(
                value=Money(cents=500),
                description="small",
                categories=[categories.category("aldi")],
            ),
            Transaction(
                value=Money(cents=5000),
                description="large",
                categories=[categories.category("aldi")],
            ),
            Transaction(
                value=Money(cents=3000),
                description="medium",
                categories=[categories.category("kaufland")],
            ),
        ]

        pred = compile_predicate("is_groceries AND value > 20.0")
        expensive = [t for t in transactions if pred(t)]

        assert len(expensive) == 2

    def test_exclude_specific_store(self, categories):
        """Test excluding specific store from groceries."""
        transactions = [
            Transaction(
                value=Money(cents=1000),
                description="aldi",
                categories=[categories.category("aldi")],
            ),
            Transaction(
                value=Money(cents=1000),
                description="kaufland",
                categories=[categories.category("kaufland")],
            ),
            Transaction(
                value=Money(cents=1000),
                description="edeka",
                categories=[categories.category("edeka")],
            ),
        ]

        pred = compile_predicate("is_groceries AND (NOT is_kaufland)")
        filtered = [t for t in transactions if pred(t)]

        assert len(filtered) == 2
        assert all("kaufland" not in t.description for t in filtered)

    def test_date_range_filter(self, categories):
        """Test filtering by date range."""
        transactions = [
            Transaction(
                value=Money(cents=1000),
                description="jan",
                categories=[categories.category("groceries")],
                date=date(2025, 1, 15),
            ),
            Transaction(
                value=Money(cents=1000),
                description="feb",
                categories=[categories.category("groceries")],
                date=date(2025, 2, 15),
            ),
            Transaction(
                value=Money(cents=1000),
                description="mar",
                categories=[categories.category("groceries")],
                date=date(2025, 3, 15),
            ),
        ]

        pred = compile_predicate('date >= "01/02/2025" AND date < "01/03/2025"')
        february = [t for t in transactions if pred(t)]

        assert len(february) == 1
        assert february[0].description == "feb"
