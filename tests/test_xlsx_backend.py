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

    print(list(be.records(dt(day=1,month=1))))
