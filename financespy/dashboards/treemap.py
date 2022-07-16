from financespy.money import ZERO


def tree_map(formula, transactions, categories, params):
    category_list = formula.category_list_flat(categories, params)

    if not category_list:
        category_list = [categories.category("expenses")]

    data, parents = tree_map_aux(category_list, categories, transactions)

    return [{"data": data, "parents": parents}]


def map_row(row, transactions):
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


def tree_map_aux(category_list, categories, transactions):
    common_parent = None
    if len(category_list) > 1:
        parents = set()
        for cat in category_list:
            parents.add(cat.parent.name)
        
        if len(parents) > 1:
            raise Exception(f"Categories from list {category_list} do not share the same parent category")

        common_parent = next(parents.__iter__() )

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

    for category in category_list:
        walk(category, max_depth=2)

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

    return ("name,parent,value\n"
            + (f"{common_parent},,\n" if common_parent else "")
            + "\n".join(data)
            ), parents


def process_result(result):
    to_include = set()
    for name, parent, total in result:
        if total:
            to_include.add(parent)

    return [
        f"{name},{parent},{total}"
        for name, parent, total in result
        if total or (not parent and not total) or (name in to_include)
    ], list(to_include)
