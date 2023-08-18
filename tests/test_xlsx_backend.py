import shutil
from financespy.transaction import parse_transaction
from financespy.account import open_account
from financespy.xlsx_backend import XLSXBackend
import pytest
from .test_utils import date


@pytest.fixture
def backend(tmp_path, categories):
    shutil.copytree("./tests/resources/finances", tmp_path / "finances")
    path = tmp_path / "finances"
    back = XLSXBackend(path)
    back.categories = categories
    back.currency = "eur"

    return back


def list_records(backend_, date_):
    return [
        (str(trans.main_category()), float(trans.value))
        for trans in backend_.records(date_)
    ]


def test_open_xlsx_account(backend):
    account = open_account("./tests/resources/finances")
    records = list_records(account, date(day=3, month=1))
    expected = [("street_food", 34), ("sports", 467), ("furniture", 43)]

    assert records == expected
    assert not list(account.records(date(day=1, month=12)))


def test_list_records(backend):
    records = list_records(backend, date(day=3, month=1))
    expected = [("street_food", 34), ("sports", 467), ("furniture", 43)]

    assert records == expected
    assert not list(backend.records(date(day=1, month=12)))


def test_insert_record(backend, categories):
    backend.insert_record(
        transaction=parse_transaction("1000, aldi", categories),
        date=date(day=3, month=1),
    )
    backend.insert_record(
        transaction=parse_transaction("1000, aldi", categories),
        date=date(day=30, month=3),
    )

    jan_expected = [
        ("street_food", 34),
        ("sports", 467),
        ("furniture", 43),
        ("aldi", 1000),
    ]

    mar_expected = [("aldi", 1000)]

    assert jan_expected == list_records(backend, date(day=3, month=1))
    assert mar_expected == list_records(backend, date(day=30, month=3))
