import collections
from financespy.transaction import parse_transaction
from financespy.transaction import Transaction

class MemoryBackend:
    def __init__(self):
        self._months = collections.defaultdict(
            lambda: [ [] for i in range(0, 31)]
        )

    def insert_record(self, date, record):
        if type(record) is str:
            record = parse_transaction(record)
            
        if type(record) is not Transaction:
            raise TypeError("Supplied parameter is not a transaction")
        
        self.records(date).append(record)

    def records(self, date):
        return self._months[(date.year,date.month)][date.day]

