import collections
from datetime import datetime

from financespy.backend import Backend, CompositeBackend
from financespy.time_factory import parse_month
from financespy.transaction import Transaction, parse_transaction
from financespy.models import TransactionModel
from financespy.money import Money
import uuid


class MemoryBackend(Backend):
    def __init__(self, categories):
        super().__init__()
        self._months = collections.defaultdict(lambda: [[] for _ in range(0, 32)])
        self._records_by_id = {}
        self.categories = categories

    def insert_record(self, date, record):
        if type(record) is TransactionModel:
            record = Transaction.to_transaction(record, self.categories)

        if type(record) is str:
            record = parse_transaction(record, self.categories)

        if type(record) is not Transaction:
            raise TypeError("Supplied parameter is not a transaction")
        
        record.id = str(uuid.uuid4())
        self._records_by_id[record.id] = record

        self._months[(date.year, date.month)][date.day].append(record)

        return record.id

    def records(self, date):
        return (
            record for record in self._months[(date.year, date.month)][date.day]
            if record.id in self._records_by_id
        )
    
    def category_from(self, name):
        return self.categories.category(name)
    
    def edit_record(self, record):
        to_edit = self._records_by_id[record.id]

        if record.value:
            to_edit.value = Money(cents=record.value)

        if record.date and record.date != datetime(1970,1,1):
            to_edit.date = record.date

        if record.categories:
            to_edit.categories = record.categories

        if record.description:
            to_edit.description = record.description

    def delete_record(self, id):
        del self._records_by_id[id]


def month_iterator_from_query(month, year, backend, query):
    m = parse_month(month)
    firstday = datetime(day=1, month=m, year=year)
    lastday = datetime(day=30, month=m, year=year)  # fix wrong logic

    results = query(firstday, lastday)
    mb = MemoryBackend(backend.categories)

    for t in results:
        mb.insert_record(t.date, t)

    cb = CompositeBackend(mb, backend)
    return cb.month(month, year)
