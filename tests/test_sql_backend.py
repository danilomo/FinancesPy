from datetime import datetime

from financespy.transaction import parse_transaction
from financespy.sql_backend import SQLBackend
from financespy.sql_backend import db_object
from tests.test_utils import get_categories, dt

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
session = session_factory()

db = db_object(Base, session)

records_ = """2019-09-04;770.0, rent
2019-09-04;20.0, withdrawal
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


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [
        (parse_date(date), parse_transaction(trans, cats))
        for date, trans in recs
    ]


def test_test():
    cats = get_categories()
    backend = SQLBackend(db, 1, cats)
    Base.metadata.create_all(engine)

    for date, rec in records(cats):
        backend.insert_record(date, rec)

    weeks = backend.month("sep", 2019).weeks()
    result = [list(str(r) for r in week.records()) for week in weeks]
    print(result)
