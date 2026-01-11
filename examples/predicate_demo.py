"""Demonstration of the predicate compiler functionality."""

from datetime import date

from financespy import Money, Transaction, compile_predicate
from financespy.categories import categories_from_list

# Create category hierarchy
categories = categories_from_list(
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

# Create sample transactions
transactions = [
    Transaction(
        value=Money(cents=2550),
        description="Weekly shopping at Aldi",
        categories=[categories.category("aldi")],
        date=date(2025, 1, 15),
    ),
    Transaction(
        value=Money(cents=4500),
        description="Dinner with friends",
        categories=[categories.category("restaurant")],
        date=date(2025, 1, 20),
    ),
    Transaction(
        value=Money(cents=1200),
        description="Quick shopping at Kaufland",
        categories=[categories.category("kaufland")],
        date=date(2025, 1, 25),
    ),
    Transaction(
        value=Money(cents=8000),
        description="Electronics purchase",
        categories=[categories.category("electronics")],
        date=date(2025, 2, 5),
    ),
    Transaction(
        value=Money(cents=3200),
        description="Lunch at nice restaurant",
        categories=[categories.category("restaurant")],
        date=date(2025, 2, 10),
    ),
]


def demo():
    """Demonstrate predicate compiler usage."""
    print("=" * 60)
    print("Predicate Compiler Demonstration")
    print("=" * 60)
    print()

    # Example 1: Category filtering
    print("Example 1: Groceries (excluding Kaufland)")
    print("Predicate: is_groceries AND (NOT is_kaufland)")
    pred = compile_predicate("is_groceries AND (NOT is_kaufland)")
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.description}: {t.value}")
    print()

    # Example 2: Value filtering
    print("Example 2: Expensive transactions (> 30.00)")
    print("Predicate: value > 30.0")
    pred = compile_predicate("value > 30.0")
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.description}: {t.value}")
    print()

    # Example 3: Date range filtering
    print("Example 3: January 2025 transactions")
    print('Predicate: date >= "01/01/2025" AND date < "01/02/2025"')
    pred = compile_predicate('date >= "01/01/2025" AND date < "01/02/2025"')
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.date}: {t.description} ({t.value})")
    print()

    # Example 4: Description pattern matching
    print("Example 4: Transactions with 'shopping' in description")
    print('Predicate: description ~ ".*shopping.*"')
    pred = compile_predicate('description ~ ".*shopping.*"')
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.description}: {t.value}")
    print()

    # Example 5: Complex combination
    print("Example 5: Food transactions in January over 20.00")
    print(
        "Predicate: is_food AND (value > 20.0) AND "
        '(date >= "01/01/2025" AND date < "01/02/2025")'
    )
    pred = compile_predicate(
        "is_food AND (value > 20.0) AND "
        '(date >= "01/01/2025" AND date < "01/02/2025")'
    )
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.date}: {t.description} ({t.value}) " f"[{t.main_category()}]")
    print()

    # Example 6: Restaurant meals with specific criteria
    print("Example 6: Restaurant meals over 30.00 or with 'Dinner' in description")
    print('Predicate: is_restaurant AND (value > 30.0 OR description ~ ".*Dinner.*")')
    pred = compile_predicate(
        'is_restaurant AND (value > 30.0 OR description ~ ".*Dinner.*")'
    )
    results = [t for t in transactions if pred(t)]
    for t in results:
        print(f"  - {t.description}: {t.value}")
    print()

    print("=" * 60)
    print("Total transactions:", len(transactions))
    print("=" * 60)


if __name__ == "__main__":
    demo()
