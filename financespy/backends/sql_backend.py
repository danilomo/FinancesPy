import json
from datetime import date

import sqlalchemy
from sqlalchemy import and_

import financespy.transaction
from financespy.account import AccountMetadata
from financespy.categories import categories_from_list
from financespy.backends.memory_backend import month_iterator_from_query
from financespy.money import Money


def db_object(base):
    class DB:
        def __init__(self):
            self.Model = base
            self.Column = sqlalchemy.Column
            self.Integer = sqlalchemy.Integer
            self.BigInteger = sqlalchemy.BigInteger
            self.String = sqlalchemy.String
            self.Date = sqlalchemy.Date

    return DB()


def account_class(db):
    class Account(db.Model):
        __tablename__ = "accounts"

        id = db.Column(db.Integer, primary_key=True, autoincrement="auto")
        categories = db.Column(db.String)
        name = db.Column(db.String)
        currency = db.Column(db.String)
        user_id = db.Column(db.Integer)
        created_at = db.Column(db.Date)

    return Account


def transaction_class(db):
    class Transaction(db.Model):
        __tablename__ = "transactions"

        id = db.Column(db.Integer, primary_key=True, autoincrement="auto")
        value = db.Column(db.BigInteger)
        description = db.Column(db.String)
        categories = db.Column(db.String)
        account_id = db.Column(db.Integer)
        date = db.Column(db.Date)

    return Transaction


def read_account_metadata(session, account_id, account_class):
    query = session.query(account_class).filter(account_class.id == account_id)
    results = list(query)

    if not results:
        return None

    row = results[0]
    categories = categories_from_list(json.loads(row.categories))

    return AccountMetadata(
        categories=categories,
        currency=row.currency,
        name=row.name,
        properties={},
        backend_type="sql",
    )


class SQLBackend:
    def __init__(self, account_id, session, transaction_class):
        self.Transaction = transaction_class
        self.session = session
        self.account_id = account_id

    def insert_record(self, date, trans):
        categories = (
            ",".join(str(cat) for cat in trans.categories) if trans.categories else ""
        )

        self.session.add(
            self.Transaction(
                value=int(trans.value),
                description=trans.description,
                categories=categories,
                account_id=self.account_id,
                date=date,
            )
        )

        self.session.commit()

    def day(self, day, month, year):
        dt = date(day=day, month=month, year=year)
        result = self._query().filter(self.Transaction.date == dt)
        return (self._transaction(t) for t in result)

    def month(self, month, year):
        def query(firstday, lastday):
            iterator = self._query().filter(
                and_(
                    self.Transaction.date >= firstday.date(),
                    self.Transaction.date <= lastday.date(),
                )
            )

            return (self._transaction(t) for t in iterator)

        return month_iterator_from_query(month, year, self, query)

    def _query(self):
        return self.session.query(self.Transaction)

    def _transaction(self, t):
        categories = list(
            self.categories.category(cat) for cat in t.categories.split(",")
        )

        result = financespy.transaction.Transaction(
            value=Money(cents=t.value), categories=categories, description=t.description
        )
        result.date = t.date
        return result

    def all(self):
        return self._query().all()
