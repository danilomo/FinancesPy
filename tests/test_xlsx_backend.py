import pytest

from financespy.transaction import parse_transaction
from financespy.transaction import Transaction
from financespy.xlsx_backend import XLSXBackend
from tests.test_utils import *

def backend():
    cats = get_categories()
    return XLSXBackend("./tests/resources/finances", cats)

def test_records():
    be = backend()
    records = [
        (str(trans.main_category()), float(trans.value))
        for trans in be.records(dt(day=3,month=1))
    ]
    expected = [
        ("street_food",34),
        ("sports",467),
        ("furniture",43)
    ]

    assert records == expected

    assert not list(be.records(dt(day=1,month=12)))
