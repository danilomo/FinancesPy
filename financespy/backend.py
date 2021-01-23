import financespy.time_factory as time_factory


class Backend:

    def __init__(self):
        self._timef = time_factory.TimeFactory(self)

    def day(self, day, month, year):
        return self._timef.month(month, year).day(day)

    def month(self, month, year):
        return self._timef.month(month, year)


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
