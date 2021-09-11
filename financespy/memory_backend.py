import collections
from datetime import datetime

from financespy.backend import Backend
from financespy.backend import CompositeBackend
from financespy.time_factory import parse_month
from financespy.transaction import Transaction
from financespy.transaction import parse_transaction


class MemoryBackend(Backend):
    def __init__(self, categories):
        super().__init__()
        self._months = collections.defaultdict(
            lambda: [[] for _ in range(0, 32)]
        )
        self.categories = categories

    def insert_record(self, date, record):
        if type(record) is str:
            record = parse_transaction(
                record,
                self.categories
            )

        if type(record) is not Transaction:
            raise TypeError("Supplied parameter is not a transaction")

        self.records(date).append(record)

    def records(self, date):
        return self._months[(date.year, date.month)][date.day]

    def category_from(self, name):
        return self.categories.category(name)


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
