from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from financespy.categories import Categories, Category
from financespy.transaction import Transaction


def value(state: "State") -> None:
    state.push(state.transaction.value._cents)


def is_category(state: "State") -> None:
    category_name = state.pop()
    category = state.categories.category(category_name)

    state.push(state.transaction.matches_category(category))


def and_(state: "State") -> None:
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 and val2)


def or_(state: "State") -> None:
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 or val2)


def equals(state: "State") -> None:
    val1 = state.pop()
    val2 = state.pop()

    state.push(val1 == val2)


FUNCTIONS = {
    "value": value,
    "=": equals,
    "is_category": is_category,
    "and": and_,
    "or": or_,
}


class State:
    def __init__(
        self,
        transaction: Transaction,
        categories: Categories,
        parameters: dict[str, Any],
    ) -> None:
        self.transaction = transaction
        self.categories = categories
        self.parameters = parameters
        self.stack = []

    def pop(self) -> Any:
        return self.stack.pop()

    def push(self, element: Any) -> None:
        self.stack.append(element)


def str_to_token(string: str) -> Callable[["State"], None]:
    # check if it is a function
    if string in FUNCTIONS:
        return FUNCTIONS[string]

    if string[0] == "$":
        # TODO: Implement parameter handling for formula variables
        pass

    # try to parse as a number
    try:
        quantity = int(float(string) * 100)

        def push_elem(state: "State") -> None:
            state.push(quantity)

        return push_elem
    except ValueError:
        pass

    # ... otherwise add as a category name
    return lambda state: state.push(string)


def apply_filter(filter_expr: list[Callable[["State"], None]], state: State) -> Any:
    for token in filter_expr:
        token(state)

    return state.stack.pop()


class Formula(BaseModel):
    """
    This class is like a Python list generator for transaction records:

    [transaction for transaction in all categories in self.categories,
    that are not in self.categories_exclude if filter_expr(transaction)
    is valid]

    """

    columns: list[str] = Field(default=["sum", "cat"])
    categories: list[str] = Field(default=["main_categories"])
    categories_exclude: list[str] = Field(default_factory=list)
    filter_string: str = ""

    def category_list_flat(
        self, categories: Categories, params: dict[str, Any]
    ) -> list[Category]:
        return [categories.category(cat, params) for cat in self.categories]

    def category_list(
        self, categories: Categories, params: dict[str, Any]
    ) -> list[Category]:
        include_list = []
        for col in self.categories:
            include_list += categories.categories(col.strip(), params)

        exclude_list = []
        for col in self.categories_exclude:
            exclude_list += [cat.name for cat in categories.categories(col, params)]

        exclude_set = set(exclude_list)
        return [cat for cat in include_list if cat.name not in exclude_set]

    def predicate(
        self, categories: Categories, parameters: Optional[dict[str, Any]] = None
    ) -> Callable[[Transaction], Any]:
        if parameters is None:
            parameters = {}

        def new_predicate(transaction):
            state = State(transaction, categories, parameters)

            return apply_filter(self.filter_expr, state)

        return new_predicate

    @property
    def filter_expr(self) -> list[Callable[["State"], None]]:
        return [
            str_to_token(element.strip()) for element in self.filter_string.split(" ")
        ]
