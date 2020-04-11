from datetime import date
import financespy.transaction
from financespy.backend import CompositeBackend
from financespy.memory_backend import MemoryBackend
from financespy.time_factory import Month
from sqlalchemy import and_

ID = 1


def db_object(base, session):
    import sqlalchemy

    class DB:
        def __init__(self):
            self.Model = base
            self.Column = sqlalchemy.Column
            self.Integer = sqlalchemy.Integer
            self.BigInteger = sqlalchemy.BigInteger
            self.String = sqlalchemy.String
            self.Date = sqlalchemy.Date
            self.session = session

    return DB()


def Transaction(db):
    class Transaction_(db.Model):
        __tablename__ = 'transactions'

        id = db.Column(db.BigInteger, primary_key=True)
        value = db.Column(db.BigInteger)
        description = db.Column(db.String)
        categories = db.Column(db.String)
        account_id = db.Column(db.BigInteger)
        date = db.Column(db.Date)

        def __repr__(self):
            return str((self.id, self.value, self.description, self.date))

        __str__ = __repr__

    return Transaction_


class SQLBackend:
    def __init__(self, db, account_id, categories):
        self.Transaction = Transaction(db)
        self.db = db
        self.session = db.session
        self.account_id = account_id
        self.categories = categories

    def insert_record(self, date, trans):
        global ID
        categories = (",".join(str(cat) for cat in trans.categories)
                      if trans.categories else "")

        self.db.session.add(self.Transaction(
            id=ID,
            value=int(trans.value),
            description=trans.description,
            categories=categories,
            account_id=self.account_id,
            date=date
        ))

        ID += 1

        self.db.session.commit()

    def day(self, day, month, year):
        dt = date(day=day, month=month, year=year)
        result = self._query().filter(self.Transaction.date == dt)
        return (self._transaction(t) for t in result)

    def month(self, month, year):
        m = Month._getMonth(month)
        firstday = date(day=1, month=m, year=year)
        lastday = date(day=30, month=m, year=year)
        results = self._query().filter(
            and_(self.Transaction.date >= firstday,
                 self.Transaction.date <= lastday))

        mb = MemoryBackend(self.categories)

        for t in results:
            mb.insert_record(t.date, self._transaction(t))

        cb = CompositeBackend(mb, self)
        return cb.month(month, year)

    def _query(self):
        return self.session.query(self.Transaction)

    def _transaction(self, t):
        categories = list(self.categories.category(cat) for cat
                          in t.categories.split(","))

        return financespy.transaction.Transaction(
            value=t.value,
            categories=categories,
            description=t.description
        )

    def all(self):
        return self._query().all()
