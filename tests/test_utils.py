import datetime
from financespy.transaction import parse_transaction



def date(day, month, year=2019):
    return datetime.date(day=day, month=month, year=year)


def parse_date(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats, records_):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [(parse_date(date), parse_transaction(trans, cats)) for date, trans in recs]


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks
