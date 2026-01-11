"""Predicate compiler for filtering transactions based on expressions.

This module provides a safe expression compiler that converts predicate expressions
into callable functions for filtering transactions. Uses Python's ast module for
safe parsing without eval().

Example usage:
    >>> compiler = PredicateCompiler()
    >>> pred = compiler.compile("is_groceries AND (NOT is_kaufland)")
    >>> matching = [t for t in transactions if pred(t)]
"""

from __future__ import annotations

import ast
import operator
import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable

from financespy.exceptions import FinancesPyError

if TYPE_CHECKING:
    from financespy.transaction import Transaction


class PredicateCompilationError(FinancesPyError):
    """Raised when predicate expression compilation fails."""

    pass


class PredicateCompiler:
    """Compiles predicate expressions into transaction filter functions.

    Supported syntax:
    - Category checks: is_<category> (e.g., is_groceries, is_food)
    - Boolean operators: AND, OR, NOT
    - Value comparisons: value > 10.0, value <= 50.0, value == 25.0
    - Date comparisons: date > "20/01/2025", date <= "20/02/2025"
    - Description equality: description == "some text"
    - Description regex: description ~ ".*pattern.*"

    Examples:
        >>> compiler = PredicateCompiler()
        >>> pred = compiler.compile("is_groceries AND (NOT is_kaufland)")
        >>> pred(transaction)  # Returns True/False

        >>> pred = compiler.compile("is_restaurant AND (value > 10.0)")
        >>> filtered = [t for t in transactions if pred(t)]

        >>> pred = compiler.compile('description ~ ".*aline.*"')
        >>> pred(transaction)  # Returns True if description matches
    """

    def __init__(self) -> None:
        """Initialize the predicate compiler."""
        self._comparison_ops = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
        }

    def compile(self, expression: str) -> Callable[[Transaction], bool]:
        """Compile an expression string into a predicate function.

        Args:
            expression: Predicate expression string

        Returns:
            Function that takes a Transaction and returns boolean

        Raises:
            PredicateCompilationError: If expression is invalid
        """
        if not expression or not expression.strip():
            raise PredicateCompilationError("Expression cannot be empty")

        try:
            # Preprocess expression to valid Python syntax
            processed_expr = self._preprocess(expression)

            # Parse to AST
            tree = ast.parse(processed_expr, mode="eval")

            # Build predicate from AST
            predicate_builder = self._build_predicate(tree.body)

            # Return predicate that handles exceptions gracefully
            def predicate(transaction: Transaction) -> bool:
                try:
                    return bool(predicate_builder(transaction))
                except Exception as e:
                    raise PredicateCompilationError(
                        f"Error evaluating predicate: {e}"
                    ) from e

            return predicate

        except SyntaxError as e:
            raise PredicateCompilationError(f"Invalid expression syntax: {e}") from e
        except PredicateCompilationError:
            raise
        except Exception as e:
            raise PredicateCompilationError(f"Failed to compile expression: {e}") from e

    def _preprocess(self, expr: str) -> str:
        """Preprocess expression to convert to valid Python syntax.

        Converts:
        - AND/OR/NOT -> and/or/not
        - is_<category> -> __is_category__('<category>')
        - value/date/description -> __value__/__date__/__description__
        - description ~ "pattern" -> __regex_match__(__description__, "pattern")
        """
        # Handle regex operator ~ before other replacements
        # description ~ "pattern" -> __regex_match__(__description__, "pattern")
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

        # Replace special operands (but not if already prefixed with __)
        expr = re.sub(r"\bvalue\b", "__value__", expr)
        expr = re.sub(r"\bdate\b", "__date__", expr)
        expr = re.sub(r"\bdescription\b", "__description__", expr)

        return expr

    def _build_predicate(self, node: ast.AST) -> Callable[[Transaction], Any]:
        """Build a predicate function from an AST node.

        Args:
            node: AST node to process

        Returns:
            Function that evaluates the node for a transaction

        Raises:
            PredicateCompilationError: If node type is not supported
        """
        if isinstance(node, ast.BoolOp):
            # Handle 'and' and 'or'
            values = [self._build_predicate(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return lambda t: all(v(t) for v in values)
            elif isinstance(node.op, ast.Or):
                return lambda t: any(v(t) for v in values)
            raise PredicateCompilationError(
                f"Unsupported boolean operator: {type(node.op).__name__}"
            )

        elif isinstance(node, ast.UnaryOp):
            # Handle 'not'
            if isinstance(node.op, ast.Not):
                operand = self._build_predicate(node.operand)
                return lambda t: not operand(t)
            raise PredicateCompilationError(
                f"Unsupported unary operator: {type(node.op).__name__}"
            )

        elif isinstance(node, ast.Compare):
            # Handle comparisons
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise PredicateCompilationError("Chained comparisons not supported")

            left_getter = self._build_value_getter(node.left)
            op = node.ops[0]
            right_getter = self._build_value_getter(node.comparators[0])

            op_func = self._comparison_ops.get(type(op))
            if not op_func:
                raise PredicateCompilationError(
                    f"Unsupported comparison operator: {type(op).__name__}"
                )

            return lambda t: op_func(left_getter(t), right_getter(t))

        elif isinstance(node, ast.Call):
            # Handle function calls
            return self._handle_call(node)

        elif isinstance(node, ast.Name):
            # Handle special variables
            return self._handle_name(node)

        elif isinstance(node, ast.Constant):
            # Handle constants (Python 3.8+)
            value = node.value
            return lambda t: value

        # Python 3.7 compatibility (ast.Num, ast.Str)
        elif isinstance(node, ast.Num):
            return lambda t: node.n
        elif isinstance(node, ast.Str):
            return lambda t: node.s

        raise PredicateCompilationError(
            f"Unsupported expression type: {type(node).__name__}"
        )

    def _handle_call(self, node: ast.Call) -> Callable[[Transaction], Any]:
        """Handle function call nodes.

        Supports:
        - __is_category__('category_name')
        - __regex_match__(__description__, 'pattern')
        """
        if not isinstance(node.func, ast.Name):
            raise PredicateCompilationError("Only simple function calls supported")

        func_name = node.func.id

        if func_name == "__is_category__":
            if len(node.args) != 1:
                raise PredicateCompilationError(
                    "__is_category__ requires exactly one argument"
                )
            category = self._get_constant(node.args[0])
            return lambda t: t.matches_category(category)

        elif func_name == "__regex_match__":
            if len(node.args) != 2:
                raise PredicateCompilationError(
                    "__regex_match__ requires exactly two arguments"
                )
            value_getter = self._build_value_getter(node.args[0])
            pattern = self._get_constant(node.args[1])

            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                raise PredicateCompilationError(f"Invalid regex pattern: {e}") from e

            return lambda t: bool(compiled_pattern.search(str(value_getter(t))))

        raise PredicateCompilationError(f"Unknown function: {func_name}")

    def _handle_name(self, node: ast.Name) -> Callable[[Transaction], Any]:
        """Handle name nodes (special variables)."""
        name = node.id

        if name == "__value__":
            # Return numeric value for comparisons
            # Money objects should support float conversion
            return lambda t: float(t.value)
        elif name == "__date__":
            return lambda t: t.date
        elif name == "__description__":
            return lambda t: t.description

        raise PredicateCompilationError(f"Unknown variable: {name}")

    def _build_value_getter(self, node: ast.AST) -> Callable[[Transaction], Any]:
        """Build a value getter for comparison operands.

        Handles constants, special variables, and nested expressions.
        Attempts to parse string constants as dates.
        """
        if isinstance(node, ast.Constant):
            value = node.value
            # Try to parse as date if it's a string
            if isinstance(value, str):
                try:
                    date_value = self._parse_date(value)
                    return lambda t: date_value
                except ValueError:
                    pass
            return lambda t: value

        # Python 3.7 compatibility
        elif isinstance(node, ast.Num):
            return lambda t: node.n
        elif isinstance(node, ast.Str):
            # Try to parse as date
            # ast.Str is deprecated but kept for Python 3.7 compatibility
            str_value = getattr(node, "s", "")
            if isinstance(str_value, str):
                try:
                    date_value = self._parse_date(str_value)
                    return lambda t: date_value
                except ValueError:
                    pass
            return lambda t: str_value

        # Otherwise, build predicate normally
        return self._build_predicate(node)

    def _get_constant(self, node: ast.AST) -> Any:
        """Extract constant value from AST node.

        Args:
            node: AST node expected to be a constant

        Returns:
            Constant value

        Raises:
            PredicateCompilationError: If node is not a constant
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7
            return node.n
        elif isinstance(node, ast.Str):  # Python 3.7
            return node.s
        elif isinstance(node, ast.Name):
            # Special variables cannot be used as constants
            raise PredicateCompilationError(
                f"Cannot use variable '{node.id}' as a constant value"
            )

        raise PredicateCompilationError(
            f"Expected constant value, got {type(node).__name__}"
        )

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in various formats.

        Supported formats:
        - DD/MM/YYYY (e.g., 20/01/2025)
        - YYYY-MM-DD (e.g., 2025-01-20)
        - YYYY/MM/DD (e.g., 2025/01/20)
        - DD-MM-YYYY (e.g., 20-01-2025)

        Args:
            date_str: Date string to parse

        Returns:
            Parsed date object

        Raises:
            ValueError: If date string cannot be parsed
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

        raise ValueError(f"Unable to parse date: {date_str}")


def compile_predicate(expression: str) -> Callable[[Transaction], bool]:
    """Compile a predicate expression into a filter function.

    Convenience function that creates a PredicateCompiler and compiles
    the expression.

    Args:
        expression: Predicate expression string

    Returns:
        Function that takes a Transaction and returns boolean

    Raises:
        PredicateCompilationError: If expression is invalid

    Examples:
        >>> pred = compile_predicate("is_groceries AND (NOT is_kaufland)")
        >>> matching_transactions = [t for t in transactions if pred(t)]

        >>> pred = compile_predicate("is_groceries AND (value > 10.0)")
        >>> expensive_groceries = list(filter(pred, transactions))

        >>> pred = compile_predicate('description ~ ".*aline.*"')
        >>> aline_transactions = [t for t in transactions if pred(t)]

        >>> pred = compile_predicate(
        ...     'is_restaurant AND ("20/01/2025" > date AND date <= "20/02/2025")'
        ... )
        >>> jan_restaurants = list(filter(pred, transactions))
    """
    compiler = PredicateCompiler()
    return compiler.compile(expression)
