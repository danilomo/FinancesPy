from collections.abc import Iterator
from typing import Callable, Optional

import pandas as pd

from financespy.categories import Categories
from financespy.transaction import Transaction


def _total(iter_: list[Transaction]) -> float:
    return float(sum(t.value for t in iter_))


class PieSection:
    def __init__(self, label: str, fn: Callable[[Transaction], bool]) -> None:
        self.label = label
        self.fn = fn
        self.transactions: list[Transaction] = []
        self.next: Optional[PieSection] = None

    def add(self, transaction: Transaction) -> None:
        if self.fn(transaction):
            self.transactions.append(transaction)
            return

        if self.next is not None:
            self.next.add(transaction)

    def total(self) -> float:
        return _total(self.transactions)


def section_factory(
    categories: Categories,
) -> Callable[[str, Optional[Callable[[Transaction], bool]]], PieSection]:
    def section(
        label: str, fn: Optional[Callable[[Transaction], bool]] = None
    ) -> PieSection:
        if fn is None:

            def fn(t: Transaction) -> bool:
                return t.matches_category(categories.category(label))

        return PieSection(label, fn)

    return section


def anything_else(label: str = "Anything else") -> PieSection:
    return PieSection(label, lambda _: True)


class PieChart:
    def __init__(self, *sections: PieSection) -> None:
        self._sections = sections
        self._make_linked_list()
        self._head = sections[0]

    def add_transaction(self, trans: Transaction) -> None:
        self._head.add(trans)

    def add_transactions(self, it: Iterator[Transaction]) -> None:
        for trans in it:
            self.add_transaction(trans)

    def _make_linked_list(self) -> None:
        sections = self._sections
        sect = sections[0]

        for s in sections[1:]:
            sect.next = s
            sect = s

    def as_data_frame(self) -> pd.DataFrame:
        labels = [sc.label for sc in self._sections]
        values = [sc.total() for sc in self._sections]
        return pd.DataFrame({"values": values, "labels": labels}, index=labels)

    def add_records(self, records: Iterator[Transaction]) -> None:
        for trans in records:
            self.add_transaction(trans)

    def sections(self) -> dict[str, PieSection]:
        return {section.label: section for section in self._sections}
