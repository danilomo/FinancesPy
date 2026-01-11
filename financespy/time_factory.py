import datetime
from collections.abc import Generator, Iterator
from typing import Any, Optional, Union

from financespy.backend import Backend

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]

MONTHS_SHORT = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

_months_indexes = dict(zip(MONTHS_SHORT, range(1, 13)))


def parse_month(m: Union[str, int]) -> int:
    if isinstance(m, str) and m in _months_indexes:
        m = m.lower()
        return _months_indexes[m]

    return int(m)


class TimeFactory:
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    def month(self, month: Union[str, int], year: int) -> "MonthIterable":
        return MonthIterable(month, year, self.backend)

    def day(
        self, day: int, month: Union[str, int], year: int
    ) -> Optional["DayIterable"]:
        return self.month(month, year).day(day)


class DayIterable:
    def __init__(self, date: datetime.date, backend: Backend) -> None:
        self.date = date
        self.day = date.day
        self.backend = backend

    def __str__(self) -> str:
        return self.date.__str__()

    __repr__ = __str__

    def records(self) -> Any:
        return self.backend.records(self.date)

    def insert_record(self, record: Any) -> Any:
        return self.backend.insert_record(self.date, record)


class WeekIterable:
    def __init__(self, month: "MonthIterable", days: list[DayIterable]) -> None:
        self.month = month
        self._days = days

    def days(self) -> list[DayIterable]:
        return self._days

    def records(self) -> Generator[Any, None, None]:
        for day in self._days:
            for record in day.records():
                record.date = day.date
                yield record


class MonthIterable:
    class _MonthIterator:
        def __init__(self, m: "MonthIterable") -> None:
            self._month = m
            self._first = datetime.date(day=1, month=m.month, year=m.year)
            self._day = self._first

        def __iter__(self) -> Iterator[DayIterable]:
            return self

        def __next__(self) -> DayIterable:
            if self._day.month != self._first.month:
                raise StopIteration

            d = self._day
            self._day = self._day + datetime.timedelta(1)
            return DayIterable(d, self._month.backend)

    def __init__(self, month: Union[str, int], year: int, backend: Backend) -> None:
        self.month = parse_month(month)
        self.year = year
        self.backend = backend

    def weeks(self) -> Generator[WeekIterable, None, None]:
        current_week: list[DayIterable] = []

        for day in self.days():
            week_day = day.date.weekday()

            if week_day == 6:
                if current_week:
                    yield WeekIterable(self, current_week)
                    current_week = [day]
                else:
                    current_week = [day]
            else:
                current_week.append(day)

        if current_week:
            yield WeekIterable(self, current_week)

    def records(self) -> Generator[Any, None, None]:
        for day in self.days():
            for record in day.records():
                record.date = day.date
                yield record

    def days(self) -> "_MonthIterator":
        return MonthIterable._MonthIterator(self)

    def day(self, day: int) -> Optional[DayIterable]:
        try:
            return DayIterable(
                datetime.date(day=day, month=self.month, year=self.year), self.backend
            )
        except Exception:
            return None
