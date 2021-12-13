from financespy.account import open_account
from financespy.transaction import parse_transaction
from financespy.xlsx_backend import XLSXBackend
from tests.test_utils import dt
from tests.test_utils import get_categories


def backend(path="./tests/resources/finances"):
    cats = get_categories()
    back = XLSXBackend(path)

    back.categories = cats
    back.currency = "eur"

    return back


def list_records(be, date_):
    return [
        (str(trans.main_category()), float(trans.value)) for trans in be.records(date_)
    ]


def test_open_xlsx_account():
    account = open_account("./tests/resources/finances")

    records = list_records(account, dt(day=3, month=1))
    expected = [("street_food", 34), ("sports", 467), ("furniture", 43)]

    assert records == expected
    assert not list(account.records(dt(day=1, month=12)))


def test_list_records():
    be = backend()
    records = list_records(be, dt(day=3, month=1))
    expected = [("street_food", 34), ("sports", 467), ("furniture", 43)]

    assert records == expected
    assert not list(be.records(dt(day=1, month=12)))


def test_insert_record():
    import shutil

    shutil.copytree("./tests/resources/finances", "./finances_copy")
    be = backend("./finances_copy")

    be.insert_record(
        transaction=parse_transaction("1000, aldi", get_categories()),
        date=dt(day=3, month=1),
    )
    be.insert_record(
        transaction=parse_transaction("1000, aldi", get_categories()),
        date=dt(day=30, month=3),
    )

    jan_expected = [
        ("street_food", 34),
        ("sports", 467),
        ("furniture", 43),
        ("aldi", 1000),
    ]

    mar_expected = [("aldi", 1000)]

    assert jan_expected == list_records(be, dt(day=3, month=1))
    assert mar_expected == list_records(be, dt(day=30, month=3))

    shutil.rmtree("./finances_copy")
