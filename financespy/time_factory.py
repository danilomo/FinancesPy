import datetime

def _index(a, x):
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return True
    return False

class TimeFactory:
    def __init__(self, backend):
        self.backend = backend

    def month(self,month,year):
        return Month( month, year, self.backend )

    def day( self, day, month, year ):
        return self.month(month,year).day(day)

class Day:
    def __init__(self, date, backend):
        self.date  = date
        self.day = date.day
        self.backend = backend

    def __str__(self):
        return self.date.__str__()

    __repr__ = __str__

    def records(self):
        return self.backend.records( self.date )

    def insert_record(self, record):
        return self.backend.insert_record(self.date, record)

class Week:
    def __init__(self, month, days):
        self.month = month
        self._days  = days

    def days(self): 
        return self._days

    def records(self):
        for day in self._days:
            for record in day.records():
                record.date = day.date
                yield record

class Month:
    _months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    _months_indexes = dict(zip(_months, range(1,13)))

    def _getMonth(m):
        if isinstance(m, str) and m in Month._months_indexes:
            m = m.lower()
            return Month._months_indexes[m]

        return int(m)

    class _MonthIterator:
        def __init__( self, m ):
            self._month = m
            self._first = datetime.date( day = 1, month = m.month, year = m.year )
            self._day   = self._first

        def __iter__(self):
            return self

        def __next__( self ):
            if self._day.month != self._first.month:
                raise StopIteration

            d = self._day
            self._day = self._day + datetime.timedelta(1)
            return Day(d, self._month.backend )


    def __init__(self, month, year, backend):
        self.month     = Month._getMonth(month)
        self.year      = year
        self.backend   = backend

    def weeks(self):
        current_week = []

        for day in self.days():
            week_day = day.date.weekday()

            if week_day == 6:
                if current_week:                
                    yield Week( self, current_week )
                    current_week = [day]
                else:
                    current_week = [day]
            else:
                current_week.append(day)

        if current_week:
            yield Week( self, current_week )

    def records(self):
        for day in self.days():
            for record in day.records():
                record.date = day.date
                yield record

    def days(self):
        return Month._MonthIterator( self )

    def day(self, day):
        try:
            return Day(datetime.date(day = day, month = self.month, year = self.year), self.backend)
        except:
            return None
        

