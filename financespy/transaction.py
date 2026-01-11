from __future__ import annotations

from datetime import date
from typing import Any

import financespy.money as money
from financespy.categories import Categories, Category
from financespy.exceptions import ParseTransactionError
from financespy.models import TransactionModel
from financespy.money import Money


class Transaction:
    """Represents a financial transaction.

    Attributes:
        value: The monetary amount of the transaction
        description: Human-readable description
        categories: List of categories this transaction belongs to
        id: Optional unique identifier
        date: Transaction date
    """

    def __init__(
        self,
        value: Money | int | float | str,
        description: str,
        categories: list[Category],
        id: str | None = None,
        date: date | None = None,
    ) -> None:
        self.value = money.Money(value) if not isinstance(value, Money) else value
        self.categories = categories or []
        self.description = description
        self.id = id
        self.date = date

    def as_expense(self) -> Transaction:
        """Return a copy of this transaction as an expense (negative value)."""
        new_value = -1 * self.value.abs()
        return Transaction(
            new_value, self.description, self.categories, self.id, self.date
        )

    def as_income(self) -> Transaction:
        """Return a copy of this transaction as income (positive value)."""
        return Transaction(
            self.value.abs(), self.description, self.categories, self.id, self.date
        )

    def __repr__(self) -> str:
        categories_str = ", ".join(str(cat) for cat in self.categories)
        return f"Transaction({self.value}, '{self.description}', [{categories_str}])"

    def main_category(self) -> Category | str:
        """Return the primary category or 'uncategorized' if none."""
        return self.categories[0] if self.categories else "uncategorized"

    def add_category(self, category: Category) -> None:
        """Add a category to this transaction."""
        if category not in self.categories:
            self.categories.append(category)

    def matches_category(self, category: str | Category) -> bool:
        """Check if transaction matches the given category.

        Args:
            category: Category name or Category object to match

        Returns:
            True if transaction matches the category
        """
        for c in self.categories:
            if (hasattr(c, "matches") and c.matches(category)) or str(c) == str(
                category
            ):
                return True
        return False

    def __getattr__(self, name: str) -> Any:
        """Support dynamic is_<category> attribute access."""
        if name.startswith("is_"):
            cat_name = name[3:]
            return self.matches_category(cat_name)
        raise AttributeError(f"Transaction object has no attribute '{name}'")

    __str__ = __repr__

    def to_model_obj(self) -> TransactionModel:
        """Convert to TransactionModel for serialization."""
        return TransactionModel(
            id=self.id,
            value=int(self.value),
            date=self.date,
            description=self.description,
            categories=[str(cat) for cat in self.categories],
        )

    @staticmethod
    def to_transaction(model_obj: TransactionModel, cats: Categories) -> Transaction:
        """Create Transaction from TransactionModel.

        Args:
            model_obj: The model object to convert
            cats: Categories manager for resolving category names

        Returns:
            Transaction instance
        """
        model_obj = TransactionModel.model_validate(model_obj)
        category_list = [cats.category(name) for name in model_obj.categories]

        transaction_id = (
            str(model_obj.id) if isinstance(model_obj.id, int) else model_obj.id
        )

        if isinstance(model_obj.value, str):
            value_cents = int(float(model_obj.value))
        else:
            value_cents = model_obj.value

        return Transaction(
            id=transaction_id,
            value=Money(cents=value_cents),
            categories=category_list,
            description=model_obj.description,
            date=model_obj.date,
        )


def parse_transaction(
    record: str | list[str], categories: Categories, separator: str = ","
) -> Transaction:
    """Parse transaction data from string or list format.

    Args:
        record: Transaction data as string or list
        categories: Categories manager for resolving names
        separator: String separator for parsing (default: ',')

    Returns:
        Parsed Transaction object

    Raises:
        ParseTransactionError: If record format is invalid
    """
    if isinstance(record, str):
        values = record.split(separator)
    elif isinstance(record, list):
        values = record
    else:
        raise ParseTransactionError(
            f"{type(record).__name__} type not allowed as parameter."
        )

    values = [s.strip() for s in values if s.strip()]

    if len(values) < 2:
        raise ParseTransactionError(
            "Record must contain at least value and description"
        )

    if len(values) == 2:
        values.append(values[1])  # Use description as default category

    value = money.Money(values[0])
    description = values[1]

    category_list = list({categories.category(s) for s in values[2:]})

    return Transaction(value, description, category_list)
