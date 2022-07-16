from dataclasses import dataclass
from typing import List


def value(state):
    state.push(state.transaction.value._cents)


def is_category(state):
    category_name = state.pop()
    category = state.categories.category(category_name)

    state.push(state.transaction.matches_category(category))


def and_(state):
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 and val2)


def or_(state):
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 or val2)


def equals(state):
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 == val2)


FUNCTIONS = {
    "value": value,
    "=": equals,
    "is_category": is_category,
    "and": and_,
    "or": or_
}


class State:
    def __init__(self, transaction, categories, parameters):
        self.transaction = transaction
        self.categories = categories
        self.parameters = parameters
        self.stack = []

    def pop(self):
        return self.stack.pop()

    def push(self, element):
        self.stack.append(element)


def str_to_token(string):
    # check if it is a function
    if string in FUNCTIONS:
        return FUNCTIONS[string]

    if string[0] == "$":
        def push_parameter(state):
            value = state.parameters[string[:1]]

    # try to parse as a number
    try:
        quantity = int(float(string) * 100)

        def push_elem(state):
            state.push(quantity)
        return push_elem
    except ValueError:
        pass

    # ... otherwise add as a category name
    return lambda state: state.push(string)


def apply_filter(filter_expr, state):
    for token in filter_expr:
        token(state)

    return state.stack.pop()


@dataclass
class Formula:
    """
    This class is like a Python list generator for transaction records:

    [transaction for transaction in all categories in self.categories,
    that are not in self.categories_exclude if filter_expr(transaction)
    is valid]

    """
    columns: List[str]
    categories: List[str]
    categories_exclude: List[str]
    filter_string: str

    def category_list_flat(self, categories, params):
        return [categories.category(cat, params) for cat in self.categories]

    def category_list(self, categories, params):
        include_list = []
        for col in self.categories:
            include_list += categories.categories(col.strip(), params)

        exclude_list = []
        for col in self.categories_exclude:
            exclude_list += [
                cat.name for cat in categories.categories(col, params)]

        exclude_set = set(exclude_list)
        return [cat for cat in include_list if cat.name not in exclude_set]

    def predicate(self, categories, parameters={}):
        def new_predicate(transaction):
            state = State(transaction, categories, parameters)

            return apply_filter(self.filter_expr, state)

        return new_predicate

    @property
    def filter_expr(self):
        return [
            str_to_token(element.strip())
            for element in self.filter_string.split(" ")
        ]


EMPTY_FORMULA = Formula([], [], [], "")
