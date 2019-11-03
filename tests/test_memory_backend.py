import pytest

from financespy.transaction import parse_transaction
from financespy.transaction import Transaction
from financespy.memory_backend import MemoryBackend
from tests.test_utils import *

def test_parse_string():
    mb = MemoryBackend(get_categories())
    mb.insert_record(
        dt(10, 2),
        "10, food"
    )

    assert mb.records(dt(10,2))[0].value._cents == 1000
    assert mb.records(dt(10,2))[0].description == "food"

def test_insert_transaction_object():
    mb = MemoryBackend(get_categories())
    mb.insert_record(
        dt(10, 2),
        parse_transaction("149, groceries", get_categories())
    )

    assert mb.records(dt(10,2))[0].value._cents == 14900
    assert mb.records(dt(10,2))[0].description == "groceries"

def test_invalid_type():
    mb = MemoryBackend(get_categories())
    
    with pytest.raises(TypeError):
        mb.insert_record(dt(10,2), (100, "food"))
