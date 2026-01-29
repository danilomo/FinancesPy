"""SQL Predicate compiler for generating SQL WHERE clauses from predicate expressions.

This module provides a compiler that converts predicate expressions into SQL WHERE
clauses for database-level filtering. Supports multiple SQL dialects.

Example usage:
    >>> compiler = SQLPredicateCompiler(dialect="postgresql")
    >>> sql = compiler.compile("is_groceries AND (NOT is_kaufland)")
    >>> # Returns: "(category_membership ? 'groceries') AND (NOT category_membership ? 'kaufland')"
"""

from __future__ import annotations

import ast
import re
from datetime import date, datetime
from typing import Any, Literal

from financespy.exceptions import FinancesPyError


class SQLPredicateCompilationError(FinancesPyError):
    """Raised when SQL predicate expression compilation fails."""

    pass


SQLDialect = Literal["postgresql", "sqlite", "mysql"]


class SQLPredicateCompiler:
    """Compiles predicate expressions into SQL WHERE clauses.

    Supported syntax:
    - Category checks: is_<category> (e.g., is_groceries, is_food)
    - Boolean operators: AND, OR, NOT
    - Value comparisons: value > 10.0, value <= 50.0, value == 25.0
    - Date comparisons: date > "20/01/2025", date <= "20/02/2025"
    - Description equality: description == "some text"
    - Description regex: description ~ ".*pattern.*"

    The compiled SQL uses the category_membership JSON column for category checks.

    Examples:
        >>> compiler = SQLPredicateCompiler(dialect="postgresql")
        >>> compiler.compile("is_groceries")
        "category_membership ? 'groceries'"

        >>> compiler.compile("is_restaurant AND (value > 1000)")
        "(category_membership ? 'restaurant') AND (value > 1000)"
    """

    def __init__(self, dialect: SQLDialect = "postgresql") -> None:
        """Initialize the SQL predicate compiler.

        Args:
            dialect: SQL dialect to generate ("postgresql", "sqlite", "mysql")
        """
        self.dialect = dialect
        self._comparison_ops = {
            ast.Eq: "=",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }

    def compile(self, expression: str) -> str:
        """Compile an expression string into a SQL WHERE clause.

        Args:
            expression: Predicate expression string

        Returns:
            SQL WHERE clause string (without the WHERE keyword)

        Raises:
            SQLPredicateCompilationError: If expression is invalid
        """
        if not expression or not expression.strip():
            raise SQLPredicateCompilationError("Expression cannot be empty")

        try:
            # Preprocess expression to valid Python syntax
            processed_expr = self._preprocess(expression)

            # Parse to AST
            tree = ast.parse(processed_expr, mode="eval")

            # Build SQL from AST
            return self._build_sql(tree.body)

        except SyntaxError as e:
            raise SQLPredicateCompilationError(
                f"Invalid expression syntax: {e}"
            ) from e
        except SQLPredicateCompilationError:
            raise
        except Exception as e:
            raise SQLPredicateCompilationError(
                f"Failed to compile expression: {e}"
            ) from e

    def _preprocess(self, expr: str) -> str:
        """Preprocess expression to convert to valid Python syntax.

        Converts:
        - AND/OR/NOT -> and/or/not
        - is_<category> -> __is_category__('<category>')
        - value/date/description -> __value__/__date__/__description__
        - description ~ "pattern" -> __regex_match__(__description__, "pattern")
        """
        # Handle regex operator ~ before other replacements
        expr = re.sub(
            r'(\w+)\s*~\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
            r"__regex_match__(__\1__, \2)",
            expr,
        )

        # Replace boolean operators
        expr = re.sub(r"\bAND\b", "and", expr)
        expr = re.sub(r"\bOR\b", "or", expr)
        expr = re.sub(r"\bNOT\b", "not", expr)

        # Replace is_<category> with __is_category__('<category>')
        expr = re.sub(r"\bis_(\w+)\b", r"__is_category__('\1')", expr)

        # Replace special operands
        expr = re.sub(r"\bvalue\b", "__value__", expr)
        expr = re.sub(r"\bdate\b", "__date__", expr)
        expr = re.sub(r"\bdescription\b", "__description__", expr)

        return expr

    def _build_sql(self, node: ast.AST) -> str:
        """Build SQL expression from an AST node.

        Args:
            node: AST node to process

        Returns:
            SQL expression string

        Raises:
            SQLPredicateCompilationError: If node type is not supported
        """
        if isinstance(node, ast.BoolOp):
            # Handle 'and' and 'or'
            parts = [self._build_sql(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return "(" + " AND ".join(parts) + ")"
            elif isinstance(node.op, ast.Or):
                return "(" + " OR ".join(parts) + ")"
            raise SQLPredicateCompilationError(
                f"Unsupported boolean operator: {type(node.op).__name__}"
            )

        elif isinstance(node, ast.UnaryOp):
            # Handle 'not'
            if isinstance(node.op, ast.Not):
                # Special case: NOT is_category - use optimized SQL
                if isinstance(node.operand, ast.Call):
                    call_node = node.operand
                    if (
                        isinstance(call_node.func, ast.Name)
                        and call_node.func.id == "__is_category__"
                        and len(call_node.args) == 1
                    ):
                        category = self._get_constant(call_node.args[0])
                        return self._category_check_sql(category, negated=True)
                # General NOT handling
                operand = self._build_sql(node.operand)
                return f"(NOT {operand})"
            raise SQLPredicateCompilationError(
                f"Unsupported unary operator: {type(node.op).__name__}"
            )

        elif isinstance(node, ast.Compare):
            # Handle comparisons
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise SQLPredicateCompilationError("Chained comparisons not supported")

            left = self._build_value_sql(node.left)
            op = node.ops[0]
            right = self._build_value_sql(node.comparators[0])

            sql_op = self._comparison_ops.get(type(op))
            if not sql_op:
                raise SQLPredicateCompilationError(
                    f"Unsupported comparison operator: {type(op).__name__}"
                )

            return f"({left} {sql_op} {right})"

        elif isinstance(node, ast.Call):
            return self._handle_call(node)

        elif isinstance(node, ast.Name):
            return self._handle_name(node)

        elif isinstance(node, ast.Constant):
            return self._format_constant(node.value)

        # Python 3.7 compatibility
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.Str):
            return self._format_constant(node.s)

        raise SQLPredicateCompilationError(
            f"Unsupported expression type: {type(node).__name__}"
        )

    def _handle_call(self, node: ast.Call) -> str:
        """Handle function call nodes.

        Supports:
        - __is_category__('category_name')
        - __regex_match__(__description__, 'pattern')
        """
        if not isinstance(node.func, ast.Name):
            raise SQLPredicateCompilationError("Only simple function calls supported")

        func_name = node.func.id

        if func_name == "__is_category__":
            if len(node.args) != 1:
                raise SQLPredicateCompilationError(
                    "__is_category__ requires exactly one argument"
                )
            category = self._get_constant(node.args[0])
            return self._category_check_sql(category)

        elif func_name == "__regex_match__":
            if len(node.args) != 2:
                raise SQLPredicateCompilationError(
                    "__regex_match__ requires exactly two arguments"
                )
            field = self._build_value_sql(node.args[0])
            pattern = self._get_constant(node.args[1])
            return self._regex_sql(field, pattern)

        raise SQLPredicateCompilationError(f"Unknown function: {func_name}")

    def _handle_name(self, node: ast.Name) -> str:
        """Handle name nodes (column references)."""
        name = node.id

        if name == "__value__":
            return "value"
        elif name == "__date__":
            return "date"
        elif name == "__description__":
            return "description"

        raise SQLPredicateCompilationError(f"Unknown variable: {name}")

    def _build_value_sql(self, node: ast.AST) -> str:
        """Build SQL for a value (handles dates, constants, columns)."""
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str):
                # Try to parse as date
                date_val = self._try_parse_date(value)
                if date_val:
                    return f"'{date_val.isoformat()}'"
            return self._format_constant(value)

        elif isinstance(node, ast.Str):
            # Python 3.7 compat
            str_value = getattr(node, "s", "")
            date_val = self._try_parse_date(str_value)
            if date_val:
                return f"'{date_val.isoformat()}'"
            return self._format_constant(str_value)

        elif isinstance(node, ast.Num):
            return str(node.n)

        return self._build_sql(node)

    def _category_check_sql(self, category: str, negated: bool = False) -> str:
        """Generate SQL for category membership check.

        Args:
            category: Category name to check
            negated: If True, generate SQL for NOT is_category

        Returns:
            SQL expression for checking category membership
        """
        if self.dialect == "postgresql":
            # PostgreSQL JSONB: category_membership ? 'category'
            if negated:
                return f"(NOT category_membership ? '{category}')"
            return f"(category_membership ? '{category}')"
        elif self.dialect == "sqlite":
            # SQLite: json_extract returns the value or NULL
            # Use COALESCE to handle NULL as false for negation
            if negated:
                return f"(COALESCE(json_extract(category_membership, '$.{category}'), 0) != 1)"
            return f"(json_extract(category_membership, '$.{category}') = 1)"
        elif self.dialect == "mysql":
            # MySQL: JSON_EXTRACT with unquoting
            if negated:
                return f"(COALESCE(JSON_EXTRACT(category_membership, '$.{category}'), false) != true)"
            return f"(JSON_EXTRACT(category_membership, '$.{category}') = true)"
        else:
            # Fallback using LIKE on TEXT (less efficient)
            if negated:
                return f"(category_membership NOT LIKE '%\"{category}\": true%' OR category_membership IS NULL)"
            return f"(category_membership LIKE '%\"{category}\": true%')"

    def _regex_sql(self, field: str, pattern: str) -> str:
        """Generate SQL for regex matching.

        Args:
            field: Column name
            pattern: Regex pattern

        Returns:
            SQL expression for regex matching
        """
        # Escape single quotes in pattern
        escaped_pattern = pattern.replace("'", "''")

        if self.dialect == "postgresql":
            return f"({field} ~ '{escaped_pattern}')"
        elif self.dialect == "sqlite":
            # SQLite requires REGEXP extension or LIKE
            # Convert simple patterns to LIKE
            like_pattern = self._regex_to_like(pattern)
            if like_pattern:
                return f"({field} LIKE '{like_pattern}')"
            # Fallback: SQLite REGEXP (requires extension)
            return f"({field} REGEXP '{escaped_pattern}')"
        elif self.dialect == "mysql":
            return f"({field} REGEXP '{escaped_pattern}')"
        else:
            # Fallback to LIKE with wildcards
            return f"({field} LIKE '%{escaped_pattern}%')"

    def _regex_to_like(self, pattern: str) -> str | None:
        """Try to convert simple regex pattern to SQL LIKE pattern.

        Args:
            pattern: Regex pattern

        Returns:
            LIKE pattern if conversion is possible, None otherwise
        """
        # Simple patterns: .* -> %, . -> _
        if re.match(r"^[\.\*\w\s]+$", pattern):
            like_pattern = pattern
            like_pattern = like_pattern.replace(".*", "%")
            like_pattern = like_pattern.replace(".", "_")
            return like_pattern.replace("'", "''")
        return None

    def _format_constant(self, value: Any) -> str:
        """Format a constant value for SQL.

        Args:
            value: Constant value

        Returns:
            SQL-formatted string
        """
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, date):
            return f"'{value.isoformat()}'"
        else:
            raise SQLPredicateCompilationError(
                f"Unsupported constant type: {type(value).__name__}"
            )

    def _get_constant(self, node: ast.AST) -> Any:
        """Extract constant value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Name):
            raise SQLPredicateCompilationError(
                f"Cannot use variable '{node.id}' as a constant value"
            )

        raise SQLPredicateCompilationError(
            f"Expected constant value, got {type(node).__name__}"
        )

    def _try_parse_date(self, date_str: str) -> date | None:
        """Try to parse a string as a date.

        Args:
            date_str: String to parse

        Returns:
            Parsed date or None if not a valid date
        """
        formats = [
            "%d/%m/%Y",  # 20/01/2025
            "%Y-%m-%d",  # 2025-01-20
            "%Y/%m/%d",  # 2025/01/20
            "%d-%m-%Y",  # 20-01-2025
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None


def compile_sql_predicate(
    expression: str, dialect: SQLDialect = "postgresql"
) -> str:
    """Compile a predicate expression into a SQL WHERE clause.

    Convenience function that creates a SQLPredicateCompiler and compiles
    the expression.

    Args:
        expression: Predicate expression string
        dialect: SQL dialect ("postgresql", "sqlite", "mysql")

    Returns:
        SQL WHERE clause string (without the WHERE keyword)

    Raises:
        SQLPredicateCompilationError: If expression is invalid

    Examples:
        >>> sql = compile_sql_predicate("is_groceries AND (NOT is_kaufland)")
        >>> # PostgreSQL: "(category_membership ? 'groceries') AND (NOT (category_membership ? 'kaufland'))"

        >>> sql = compile_sql_predicate("is_groceries", dialect="sqlite")
        >>> # SQLite: "(json_extract(category_membership, '$.groceries') = true)"
    """
    compiler = SQLPredicateCompiler(dialect=dialect)
    return compiler.compile(expression)
