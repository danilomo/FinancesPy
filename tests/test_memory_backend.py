import pytest

from financespy.backends.memory_backend import MemoryBackend
from financespy.transaction import parse_transaction
from tests.test_utils import date as dt
from tests.test_utils import total_iterator, records


def test_parse_string(categories):
    backend = MemoryBackend(categories)
    backend.insert_record(dt(10, 2), "10, food")

    assert backend.records(dt(10, 2))[0].value._cents == 1000
    assert backend.records(dt(10, 2))[0].description == "food"


def test_insert_transaction_object(categories):
    backend = MemoryBackend(categories)
    backend.insert_record(dt(10, 2), parse_transaction("149, groceries", categories))

    assert backend.records(dt(10, 2))[0].value._cents == 14900
    assert backend.records(dt(10, 2))[0].description == "groceries"


def test_invalid_type(categories):
    mb = MemoryBackend(categories)

    with pytest.raises(TypeError):
        mb.insert_record(dt(10, 2), (100, "food"))


RECORDS = """2019-09-04;20.0, withdrawal
2019-09-05;20.58, rewe
2019-09-06;49.28, aldi
2019-09-08;17.05, müller
2019-09-08;97.2, monthly_ticket
2019-09-11;50.0, withdrawal
2019-09-13;50.0, lidl
2019-09-19;40.0, h_&_m
2019-09-20;55.58, lidl
2019-09-21;50.0, withdrawal
2019-09-21;25.0, train_ticket"""

RECORDS_FILTERED = """2019-09-04;20.0, withdrawal
2019-09-05;20.58, rewe
2019-09-06;49.28, aldi
2019-09-08;17.05, müller
2019-09-08;97.2, monthly_ticket
2019-09-11;50.0, withdrawal
2019-09-19;40.0, h_&_m
2019-09-21;50.0, withdrawal
2019-09-21;25.0, train_ticket"""


def test_copy_from(categories):
    cats = categories
    mb_from = MemoryBackend(cats)
    mb_to = MemoryBackend(cats)
    mb_expected = MemoryBackend(cats)

    not_lidl = [lambda t: not t.is_lidl]

    for date, trans in records(cats, RECORDS):
        mb_from.insert_record(date, trans)

    for date, trans in records(cats, RECORDS_FILTERED):
        mb_expected.insert_record(date, trans)

    mb_to.copy_from(mb_from, year=2019, filters=not_lidl)

    weeks1 = mb_expected.month("sep", 2019).weeks()
    weeks2 = mb_to.month("sep", 2019).weeks()

    print(f"{total_iterator(weeks1)}")
    print(f"{total_iterator(weeks2)}")

    assert total_iterator(weeks1) == total_iterator(weeks2)

    month1 = mb_expected.month("sep", 2019).days()
    month2 = mb_to.month("sep", 2019).days()

    print(f"{total_iterator(month1)}")
    print(f"{total_iterator(month2)}")

    assert total_iterator(month1) == total_iterator(month2)
