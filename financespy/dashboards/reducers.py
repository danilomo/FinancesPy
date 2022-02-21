import math
import sys
from financespy.money import ZERO, Money


def min():
    min_value = Money(cents=sys.maxsize)

    def func(value):
        nonlocal min_value

        if value < min_value:
            min_value = value

    def total():
        nonlocal min_value

        if min_value == Money(cents=sys.maxsize):
            return ZERO

        return min_value

    return func, total


def max():
    max_value = Money(cents=-sys.maxsize)

    def func(value):
        nonlocal max_value

        if value > max_value:
            max_value = value

    def total():
        nonlocal max_value

        if max_value == Money(cents=-sys.maxsize):
            return ZERO

        return max_value

    return func, total


def sum():
    counter_value = ZERO

    def func(value):
        nonlocal counter_value
        counter_value += value

    return func, lambda: counter_value


def counter():
    counter_value = 0

    def func(value):
        nonlocal counter_value
        counter_value += 1

    return func, lambda: counter_value


reducers = {
    "sum": sum,
    "max": max,
    "min": min,
    "counter": counter,
}


def new_reducer(name):
    reducerf = reducers.get(name, None)

    if not reducerf:
        return None

    update, total = reducerf()

    return Reducer(update, total)


class Reducer:
    def __init__(self, update, total):
        self.updatef = update
        self.totalf = total

    def add(self, value):
        self.updatef(value)

    def total(self):
        return self.totalf()
