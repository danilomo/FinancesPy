import pytest

from financespy.account import MemoryBackend
from financespy.dashboards import Formula
from financespy.money import Money
from tests.test_utils import records

_RECORDS = """2019-09-04;20.0, withdrawal
2019-09-05;20.58, rewe
2019-09-06;49.28, aldi
2019-09-08;17.05, rewe
2019-09-08;97.2, monthly_ticket
2019-09-11;50.0, withdrawal
2019-09-13;50.0, lidl
2019-09-19;40.0, aldi
2019-09-20;55.58, lidl
2019-09-21;50.0, withdrawal
2019-09-21;25.0, train_ticket"""


@pytest.fixture
def account(categories):
    backend = MemoryBackend(categories)

    for date_, trans in records(categories, _RECORDS):
        backend.insert_record(date_, trans)

    return backend


def test_formula(account):
    formula = Formula(
        columns=[],
        categories=["rewe", "aldi"],
        categories_exclude=[],
        filter_string="value 50 = lidl is_category or",
    )
    predicate = formula.predicate(account.categories)

    def all_records_2019():
        for week in account.month("sep", 2019).weeks():
            for time in week.records():
                if not predicate(time):
                    continue

                yield time

    for record in all_records_2019():
        assert record.value == Money(50) or record.is_lidl


def test_formula_with_parameter(account):
    formula = Formula(
        columns=[],
        categories=["rewe", "aldi"],
        categories_exclude=[],
        filter_string="value 50 = lidl is_category or",
    )
    predicate = formula.predicate(account.categories)

    def all_records_2019():
        for week in account.month("sep", 2019).weeks():
            for time in week.records():
                if not predicate(time):
                    continue

                yield time

    for record in all_records_2019():
        assert record.value == Money(50) or record.is_lidl
