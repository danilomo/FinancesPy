import os
from datetime import datetime

try:

    from financespy.account import open_account
    from financespy.backends.memory_backend import MemoryBackend
    from financespy.transaction import parse_transaction

    _gnucash_module_loaded = True
except ImportError:
    _gnucash_module_loaded = False

records_ = """2019-09-04;20.0, Books
2019-09-05;20.58, Cable
2019-09-06;49.28, Clothes
2019-09-08;17.05, Gifts
2019-09-08;97.2, Hobbies
2019-09-11;50.0, Phone
2019-09-13;50.0, Cable
2019-09-19;40.0, Phone
2019-09-20;55.58, Dining
2019-09-21;50.0, Charity
2019-09-21;25.0, Charity"""


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [(parse_date(date), parse_transaction(trans, cats)) for date, trans in recs]


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks


def test_insert_records():
    if not _gnucash_module_loaded:
        return

    os.system("cp -R ./tests/resources/gnucash ./gnucash")

    try:
        account = open_account("./gnucash/myacc.gnucash")

        backend = account.backend
        session = account.backend._session
        categories = backend.categories
        memory_backend = MemoryBackend(categories)

        # populating backends
        for date, rec in records(categories):
            backend.insert_record(date, rec)
            memory_backend.insert_record(date, rec)

        # assert we read the same in both backends
        weeks1 = backend.month("sep", 2019).weeks()
        weeks2 = memory_backend.month("sep", 2019).weeks()

        assert total_iterator(weeks1) == total_iterator(weeks2)

        month1 = backend.month("sep", 2019).days()
        month2 = memory_backend.month("sep", 2019).days()

        assert total_iterator(month1) == total_iterator(month2)

        session.save()
        session.end()
    finally:
        os.system("rm -rf ./gnucash")
