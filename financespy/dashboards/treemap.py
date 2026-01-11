from typing import Any

from financespy.categories import Categories, Category
from financespy.dashboards.formula import Formula
from financespy.money import ZERO
from financespy.transaction import Transaction


def transaction_in_list(transaction: Transaction, categories: list[Category]) -> bool:
    for cat in categories:
        if transaction.matches_category(cat):
            return True

    return False


def tree_map(
    formula: Formula,
    transactions: list[Transaction],
    categories: Categories,
    params: dict,
) -> list[dict]:
    category_list = formula.category_list_flat(categories, params)

    if not category_list:
        category_list = [categories.category("expenses")]

    data, parents = tree_map_aux(
        categories,
        [trans for trans in transactions if transaction_in_list(trans, category_list)],
    )

    return [{"data": data, "parents": parents}]


def map_row(row: tuple[Category, bool], transactions: list[Transaction]) -> list[Any]:
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


def tree_map_aux(
    categories: Categories,
    transactions: list[Transaction],
) -> tuple[str, list[str]]:
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

    walk(categories.category("expenses"), max_depth=2)

    rows = [map_row(row, transactions) for row in rows]

    result = []
    for row in rows:
        name, parent, total, is_leaf = row

        if parent is None:
            result.append((name, "", ""))
            continue
        if not is_leaf:
            result.append((name, parent, ""))
            continue
        if is_leaf and total == ZERO:
            continue
        result.append((name, parent, total))

    data, parents = process_result(result)

    print(data, parents)

    return ("name,parent,value\n" + "\n".join(data)), parents


def process_result(result: list[tuple[str, str, Any]]) -> tuple[list[str], list[str]]:
    to_include: set[str] = set()
    for _name, parent, total in result:
        if total:
            to_include.add(parent)

    return [
        f"{name},{parent},{total}"
        for name, parent, total in result
        if total or (not parent and not total) or (name in to_include)
    ], list(to_include)
