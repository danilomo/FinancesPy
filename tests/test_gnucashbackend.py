import os
from datetime import datetime
from gnucash import Session
from financespy.gnucash_backend import GnucashBackend
from financespy.gnucash_backend import categories_from
from financespy.transaction import parse_transaction
from financespy.memory_backend import MemoryBackend


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
    return [
        (parse_date(date), parse_transaction(trans, cats))
        for date, trans in recs
    ]


def total_iterator(iterator):
    weeks = [
        sum(t.value for t in element.records()) for element in iterator
    ]

    return weeks


def test_insert_records():
    os.system("cp -R ./tests/resources/gnucash ./gnucash")

    # setting up gnucash backend
    session = Session('./gnucash/myacc.gnucash')
    assets = session.book.get_root_account()["Assets"]
    checking_account = assets["Current Assets"]["Checking Account"]
    expenses_account = session.book.get_root_account()["Expenses"]
    categories = categories_from(expenses_account)

    # creating backends
    backend = GnucashBackend(
        session=session,
        account=checking_account,
        categories=categories,
        currency="EUR"
    )

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
    os.system("rm -rf ./gnucash")


def aaa_test_listrecords():
    session = Session('/home/danilo/Documents/my_account.gnucash')
    assets = session.book.get_root_account()["Assets"]
    checking_account = assets["Current Assets"]["Checking Account"]
    expenses_account = session.book.get_root_account()["Expenses"]
    categories = categories_from(expenses_account)
    backend = GnucashBackend(session, checking_account, categories)

    for t in backend.month(month=9, year=2019).records():
        print((t, t.date))

    session.end()
