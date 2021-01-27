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

    def copy_year(self, account, year, tags=[], filters=[]):
        for month in range(1, 13):
            for trans in account.month(month, year=year).records():
                matches_some_filter = False

                for f in filters:
                    if trans.matches_category(f):
                        matches_some_filter = True
                        break

                if matches_some_filter:
                    continue

                for t in tags:
                    cat = self._backend.category_from(t)
                    trans.add_category(cat)

                self.insert_record(trans.date, trans)
