import sys
from typing import Any, Callable, Optional, Union

from financespy.money import ZERO, Money


def min() -> tuple[Callable[[Money], None], Callable[[], Money]]:
    min_value = Money(cents=sys.maxsize)

    def func(value: Money) -> None:
        nonlocal min_value

        if value < min_value:
            min_value = value

    def total() -> Money:
        if min_value == Money(cents=sys.maxsize):
            return ZERO

        return min_value

    return func, total


def max() -> tuple[Callable[[Money], None], Callable[[], Money]]:
    max_value = Money(cents=-sys.maxsize)

    def func(value: Money) -> None:
        nonlocal max_value

        if value > max_value:
            max_value = value

    def total() -> Money:
        if max_value == Money(cents=-sys.maxsize):
            return ZERO

        return max_value

    return func, total


def sum() -> tuple[Callable[[Money], None], Callable[[], Money]]:
    counter_value = ZERO

    def func(value: Money) -> None:
        nonlocal counter_value
        counter_value += value

    return func, lambda: counter_value


def counter() -> tuple[Callable[[Money], None], Callable[[], int]]:
    counter_value = 0

    def func(value: Money) -> None:
        nonlocal counter_value
        counter_value += 1

    return func, lambda: counter_value


reducers = {
    "sum": sum,
    "max": max,
    "min": min,
    "counter": counter,
}


def new_reducer(name: str) -> Optional["Reducer"]:
    reducerf = reducers.get(name, None)

    if not reducerf:
        return None

    update, total = reducerf()

    return Reducer(update, total)


class CategoryReducer:
    def __init__(self, category: str) -> None:
        self.category = category

    def add(self, value: Money) -> None:
        # This method is intentionally empty as CategoryReducer is a base class
        # Specific implementations should override this method
        pass

    def total(self) -> str:
        return self.category


class Reducer:
    def __init__(
        self, update: Callable[[Money], None], total: Callable[[], Union[Money, int]]
    ) -> None:
        self.updatef = update
        self.totalf = total

    def add(self, value: Money) -> None:
        self.updatef(value)

    def total(self) -> Any:
        result = self.totalf()
        if isinstance(result, int):
            return result
        else:
            return result._cents
