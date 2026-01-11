import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import financespy.account as acc
from financespy.backends.memory_backend import MemoryBackend
from financespy.backends.sql_backend import (
    Account,
    Base,
    SQLBackend,
    read_account_metadata,
)
from financespy.transaction import parse_transaction

from .test_utils import parse_date


@pytest.fixture
def records(categories):
    RECORDS = """2019-09-04;20.0, withdrawal
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
    recs = (tuple(line.split(";")) for line in RECORDS.split("\n"))
    return [
        (parse_date(date.strip()), parse_transaction(trans, categories))
        for date, trans in recs
    ]


@pytest.fixture
def account(category_list, categories):
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    test_account = Account(
        name="savings",
        currency="eur",
        categories=json.dumps(category_list),
        user_id=1,
        created_at=parse_date("2023-01-01"),
    )
    session.add(test_account)
    session.commit()
    account_data = read_account_metadata(session, 1)
    backend = SQLBackend(
        account_id=1,
        session=session,
        categories=categories,
    )

    if account_data is None:
        raise ValueError("Failed to read account metadata")
    return acc.Account(backend, account_data)


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks


def test_month_iterator(account, records):
    backend = account.backend

    cats = backend.categories
    memory_backend = MemoryBackend(cats)

    for date, rec in records:
        backend.insert_record(date, rec)
        memory_backend.insert_record(date, rec)

    weeks1 = backend.month("sep", 2019).weeks()
    weeks2 = memory_backend.month("sep", 2019).weeks()

    assert total_iterator(weeks1) == total_iterator(weeks2)

    month1 = backend.month("sep", 2019).days()
    month2 = memory_backend.month("sep", 2019).days()

    assert total_iterator(month1) == total_iterator(month2)
