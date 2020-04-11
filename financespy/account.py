import datetime

_current_year = datetime.datetime.now().year


class Account:
    def __init__(self, backend):
        self._backend = backend

    def day(self, day, month, year=_current_year):
        return self._backend.day(day, month, year)

    def month(self, month, year=_current_year):
        return self._backend.month(month, year)

    def insert_record(self, date, transaction):
        self._backend.insert_record(date, transaction)
