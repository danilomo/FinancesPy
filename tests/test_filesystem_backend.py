import os
from datetime import datetime

from financespy.account import open_account
from financespy.transaction import parse_transaction
from financespy.xlsx_backend import XLSXBackend
from financespy.memory_backend import MemoryBackend
from tests.test_utils import get_categories
from tests.test_utils import dt


_records = """2019-09-04;20.0, withdrawal
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


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats, records_):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [
        (parse_date(date), parse_transaction(trans, cats))
        for date, trans in recs
    ]


def total_iterator(iterator):
    weeks = [
        sum(t.value for t in element.records()) for element in iterator
    ]

    return weeks


def test_copy_from():
    account = open_account("./tests/resources/finances_csv/")
    
    cats = get_categories()
    mb = MemoryBackend(cats)
    mb_expected = MemoryBackend(cats)

    mb.copy_from(account.backend, year=2019)

    for date, trans in records(cats, _records):
        mb_expected.insert_record(date, trans)

    weeks1 = mb.month("sep", 2019).weeks()
    weeks2 = mb_expected.month("sep", 2019).weeks()

    print(f"{total_iterator(weeks1)}")
    print(f"{total_iterator(weeks2)}")

    assert total_iterator(weeks1) == total_iterator(weeks2)

    month1 = mb.month("sep", 2019).days()
    month2 = mb_expected.month("sep", 2019).days()

    print(f"{total_iterator(month1)}")
    print(f"{total_iterator(month2)}")

    assert total_iterator(month1) == total_iterator(month2)
