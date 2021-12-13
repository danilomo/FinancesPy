import json
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import financespy.account as account
from financespy.memory_backend import MemoryBackend
from financespy.sql_backend import SQLBackend
from financespy.sql_backend import db_object
from financespy.sql_backend import read_account_metadata
from financespy.sql_backend import transaction_class, account_class
from financespy.transaction import parse_transaction
from tests.test_utils import get_categories_as_list

records_ = """2019-09-04;20.0, withdrawal
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

base = declarative_base()
db = db_object(base)
Transaction = transaction_class(db)
Account = account_class(db)

categories = get_categories_as_list()


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [(parse_date(date), parse_transaction(trans, cats)) for date, trans in recs]


def open_sql_account():
    engine = create_engine("sqlite:///:memory:", echo=True)
    base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    test_account = Account(
        name="savings", currency="eur", categories=json.dumps(categories), user_id=1
    )
    session.add(test_account)
    session.commit()

    account_data = read_account_metadata(session, 1, Account)

    backend = SQLBackend(session=session, account_id=1, transaction_class=Transaction)

    return account.Account(backend, account_data)


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks


def test_month_iterator():
    account = open_sql_account()

    backend = account.backend
    cats = backend.categories
    memory_backend = MemoryBackend(cats)

    for date, rec in records(cats):
        backend.insert_record(date, rec)
        memory_backend.insert_record(date, rec)

    weeks1 = backend.month("sep", 2019).weeks()
    weeks2 = memory_backend.month("sep", 2019).weeks()

    assert total_iterator(weeks1) == total_iterator(weeks2)

    month1 = backend.month("sep", 2019).days()
    month2 = memory_backend.month("sep", 2019).days()

    assert total_iterator(month1) == total_iterator(month2)
