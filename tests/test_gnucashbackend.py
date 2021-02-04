from datetime import datetime
from gnucash import Session
from financespy.gnucash_backend import GnucashBackend
from financespy.gnucash_backend import categories_from
from financespy.memory_backend import MemoryBackend
from financespy.transaction import parse_transaction

records_ = """2019-09-04;20.0, Books
2019-09-05;20.58, Books
2019-09-06;49.28, Books
2019-09-08;17.05, Books"""


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [
        (parse_date(date), parse_transaction(trans, cats))
        for date, trans in recs
    ]


def aaatest_insertrecord():
    session = Session('/home/danilo/Documents/my_account.gnucash')
    checking_account = session.book.get_root_account()["Assets"]["Current Assets"]["Checking Account"]
    expenses_account = session.book.get_root_account()["Expenses"]
    categories = categories_from(expenses_account)
    backend = GnucashBackend(session, checking_account, categories)

    for date, rec in records(categories):
        backend.insert_record(date, rec)

    session.save()
    session.end()

def test_listrecords():
    session = Session('/home/danilo/Documents/my_account.gnucash')
    checking_account = session.book.get_root_account()["Assets"]["Current Assets"]["Checking Account"]
    expenses_account = session.book.get_root_account()["Expenses"]
    categories = categories_from(expenses_account)
    backend = GnucashBackend(session, checking_account, categories)

    for t in backend.month(month=9,year=2019).records():
        print((t, t.date))

    session.end()    
