import collections
from financespy.transaction import parse_transaction
from financespy.transaction import Transaction
from financespy.backend import Backend


class MemoryBackend(Backend):
    def __init__(self, categories):
        super().__init__()
        self._months = collections.defaultdict(
            lambda: [[] for i in range(0, 32)]
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
