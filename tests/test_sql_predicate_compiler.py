"""Tests for the SQL predicate compiler."""

import pytest

from financespy.sql_predicate_compiler import (
    SQLPredicateCompiler,
    SQLPredicateCompilationError,
    compile_sql_predicate,
)


class TestSQLPredicateCompilerPostgreSQL:
    """Test SQL predicate compiler with PostgreSQL dialect."""

    @pytest.fixture
    def compiler(self):
        return SQLPredicateCompiler(dialect="postgresql")

    def test_simple_category_check(self, compiler):
        result = compiler.compile("is_groceries")
        assert result == "(category_membership ? 'groceries')"

    def test_not_category(self, compiler):
        result = compiler.compile("NOT is_restaurant")
        # Optimized NOT uses direct negation syntax
        assert result == "(NOT category_membership ? 'restaurant')"

    def test_and_categories(self, compiler):
        result = compiler.compile("is_groceries AND is_food")
        assert "(category_membership ? 'groceries')" in result
        assert "(category_membership ? 'food')" in result
        assert " AND " in result

    def test_or_categories(self, compiler):
        result = compiler.compile("is_groceries OR is_restaurant")
        assert "(category_membership ? 'groceries')" in result
        assert "(category_membership ? 'restaurant')" in result
        assert " OR " in result

    def test_complex_expression(self, compiler):
        result = compiler.compile("is_groceries AND (NOT is_kaufland)")
        assert "(category_membership ? 'groceries')" in result
        assert "(NOT category_membership ? 'kaufland')" in result
        assert " AND " in result

    def test_value_comparison_gt(self, compiler):
        result = compiler.compile("value > 1000")
        assert result == "(value > 1000)"

    def test_value_comparison_lte(self, compiler):
        result = compiler.compile("value <= 50.5")
        assert result == "(value <= 50.5)"

    def test_description_equality(self, compiler):
        result = compiler.compile('description == "test"')
        assert result == "(description = 'test')"

    def test_description_regex(self, compiler):
        result = compiler.compile('description ~ ".*pattern.*"')
        assert result == "(description ~ '.*pattern.*')"

    def test_date_comparison(self, compiler):
        result = compiler.compile('date > "20/01/2025"')
        assert result == "(date > '2025-01-20')"

    def test_combined_category_and_value(self, compiler):
        result = compiler.compile("is_restaurant AND (value > 2000)")
        assert "(category_membership ? 'restaurant')" in result
        assert "(value > 2000)" in result
        assert " AND " in result

    def test_complex_nested_expression(self, compiler):
        result = compiler.compile(
            "(is_groceries OR is_restaurant) AND (NOT is_lidl) AND (value > 500)"
        )
        assert "(category_membership ? 'groceries')" in result
        assert "(category_membership ? 'restaurant')" in result
        assert "(NOT category_membership ? 'lidl')" in result
        assert "(value > 500)" in result

    def test_empty_expression_raises_error(self, compiler):
        with pytest.raises(SQLPredicateCompilationError):
            compiler.compile("")

    def test_invalid_syntax_raises_error(self, compiler):
        with pytest.raises(SQLPredicateCompilationError):
            compiler.compile("is_groceries AND AND is_food")


class TestSQLPredicateCompilerSQLite:
    """Test SQL predicate compiler with SQLite dialect."""

    @pytest.fixture
    def compiler(self):
        return SQLPredicateCompiler(dialect="sqlite")

    def test_simple_category_check(self, compiler):
        result = compiler.compile("is_groceries")
        # SQLite uses = 1 for boolean true
        assert result == "(json_extract(category_membership, '$.groceries') = 1)"

    def test_not_category(self, compiler):
        result = compiler.compile("NOT is_restaurant")
        # Uses COALESCE to handle NULL properly
        expected = "(COALESCE(json_extract(category_membership, '$.restaurant'), 0) != 1)"
        assert result == expected

    def test_and_categories(self, compiler):
        result = compiler.compile("is_groceries AND is_food")
        assert "json_extract(category_membership, '$.groceries') = 1" in result
        assert "json_extract(category_membership, '$.food') = 1" in result
        assert " AND " in result


class TestSQLPredicateCompilerMySQL:
    """Test SQL predicate compiler with MySQL dialect."""

    @pytest.fixture
    def compiler(self):
        return SQLPredicateCompiler(dialect="mysql")

    def test_simple_category_check(self, compiler):
        result = compiler.compile("is_groceries")
        assert result == "(JSON_EXTRACT(category_membership, '$.groceries') = true)"

    def test_regex_match(self, compiler):
        result = compiler.compile('description ~ "pattern"')
        assert result == "(description REGEXP 'pattern')"


class TestCompileSQLPredicateConvenience:
    """Test the convenience function."""

    def test_default_dialect_is_postgresql(self):
        result = compile_sql_predicate("is_groceries")
        assert result == "(category_membership ? 'groceries')"

    def test_explicit_dialect(self):
        result = compile_sql_predicate("is_groceries", dialect="sqlite")
        assert "json_extract" in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def compiler(self):
        return SQLPredicateCompiler(dialect="postgresql")

    def test_category_with_underscore(self, compiler):
        result = compiler.compile("is_asia_market")
        assert result == "(category_membership ? 'asia_market')"

    def test_single_quotes_escaped_in_description(self, compiler):
        result = compiler.compile("description == \"it's a test\"")
        assert "it''s a test" in result

    def test_multiple_date_formats(self, compiler):
        # DD/MM/YYYY
        result1 = compiler.compile('date > "20/01/2025"')
        assert "'2025-01-20'" in result1

        # YYYY-MM-DD
        result2 = compiler.compile('date > "2025-01-20"')
        assert "'2025-01-20'" in result2

    def test_boolean_precedence(self, compiler):
        # AND has higher precedence than OR
        result = compiler.compile("is_a OR is_b AND is_c")
        # Should be: is_a OR (is_b AND is_c)
        assert " OR " in result
        assert " AND " in result
