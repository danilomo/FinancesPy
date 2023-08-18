from datetime import date

from financespy.account import open_account
from financespy.dashboards import open_dashboard
from financespy.money import ZERO

account = open_account("/home/danilo/Documents/Finances/accounts/savings")
dashb = open_dashboard(
    "/home/danilo/Documents/Finances/dashboards/monthly_dashboard.yaml"
)

transactions = list(
    account.transactions(
        date_from=date(year=2020, month=1, day=1),
        date_to=date(year=2020, month=2, day=1),
    )
)


categories = account.backend.categories


def tree_map(categories, transactions):
    rows = []

    def walk(cat, max_depth=3, level=0):
        children = categories.children(cat)

        if not children or level == max_depth:
            rows.append([cat, True])
            return
        else:
            rows.append([cat, False])

        for child in children:
            walk(child, max_depth, level + 1)

    def map_row(row):
        cat, is_leaf = row
        parent = cat.parent.name if cat.parent else None

        if not is_leaf:
            return [cat.name, cat.parent, ZERO, None]

        total = ZERO

        for t in transactions:
            if not t.matches_category(cat):
                continue

            total += t.value

        return [cat.name, parent, total, is_leaf]

    walk(categories.category("expenses"), max_depth=2)

    rows = [map_row(row) for row in rows]

    result = []
    for row in rows:
        name, parent, total, is_leaf = row

        if parent is None:
            result.append(f"{name},,")
            continue

        if not is_leaf:
            result.append(f"{name}, {parent},")
            continue

        if is_leaf and total == ZERO:
            continue

        result.append(f"{name}, {parent}, {total}")

    return "\n".join(result)


print(tree_map(categories, transactions))
