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

    def copy_year(self, account, year):
        for month in range(1, 13):
            for trans in account.month(month, year=year).records():
                self.insert_record(trans.date, trans)
