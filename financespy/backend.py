import financespy.time_factory as time_factory


def _satisfy_filters(record, filters):
    if not filters:
        return True
    num_filters = len(filters)
    test_all = (f(record) for f in filters)
    return num_filters == sum(test_all)


class Backend:
    def __init__(self):
        self._timef = time_factory.TimeFactory(self)

    def day(self, day, month, year):
        return self.timef.month(month, year).day(day)

    def month(self, month, year):
        return self._timef.month(month, year)

    def copy_from(self, backend, year, filters=[]):
        for month in range(1, 13):
            month_iterator = backend.month(month, year)

            for record in month_iterator.records():
                if _satisfy_filters(record, filters):
                    self.insert_record(record.date, record)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Empty exit method for allowing any backend to be used in a with block"""
        pass


class CompositeBackend:
    def __init__(self, readbe, writebe):
        self._readbe = readbe
        self._writebe = writebe

    def day(self, day, month, year):
        return self._readbe.day(day, month, year)

    def month(self, month, year):
        return self._readbe.month(month, year)

    def insert_record(self, date, transaction):
        self._writebe.insert_record(date, transaction)
