from datetime import date
import financespy.transaction
from financespy.backend import CompositeBackend
from financespy.money import Money
from financespy.memory_backend import MemoryBackend
from financespy.memory_backend import month_iterator_from_query
from sqlalchemy import and_


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
    class TransactionInner(db.Model):
        __tablename__ = 'transactions'

        id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
        value = db.Column(db.BigInteger)
        description = db.Column(db.String)
        categories = db.Column(db.String)
        account_id = db.Column(db.Integer)
        date = db.Column(db.Date)

        def __repr__(self):

            # TODO: better string representation
            return str((self.id, self.value, self.description, self.date))

        __str__ = __repr__

    return TransactionInner


class SQLBackend:
    def __init__(self, db, account_id, categories):
        self.Transaction = Transaction(db)
        self.db = db
        self.session = db.session
        self.account_id = account_id
        self.categories = categories


    def insert_record(self, date, trans):
        categories = (",".join(str(cat) for cat in trans.categories)
                      if trans.categories else "")

        self.db.session.add(self.Transaction(
            value=int(trans.value),
            description=trans.description,
            categories=categories,
            account_id=self.account_id,
            date=date
        ))

        self.db.session.commit()


    def day(self, day, month, year):
        dt = date(day=day, month=month, year=year)
        result = self._query().filter(self.Transaction.date == dt)
        return (self._transaction(t) for t in result)


    def month(self, month, year):
        def query(firstday, lastday):
            iterator = self._query().filter(
                and_(self.Transaction.date >= firstday.date(),
                     self.Transaction.date <= lastday.date()))

            return (self._transaction(t) for t in iterator)
            
        return month_iterator_from_query(month, year, self, query)


    def _query(self):
        return self.session.query(self.Transaction)


    def _transaction(self, t):
        categories = list(self.categories.category(cat) for cat
                          in t.categories.split(","))

        result = financespy.transaction.Transaction(
            value=Money(cents=t.value),
            categories=categories,
            description=t.description
        )
        result.date = t.date
        return result


    def all(self):
        return self._query().all()
