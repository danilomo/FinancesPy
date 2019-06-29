import collections

class MemoryBackend:
    def __init__(self):
        self._months = collections.defaultdict(
            lambda: [ [] for i in range(0, 31)]
        )

    def insert_record(self, date, record):
        self.records(date).append(record)

    def records(self, date):
        return self._months[(date.year,date.month)][date.day]

