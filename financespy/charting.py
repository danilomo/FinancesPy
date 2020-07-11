import pandas as pd


def _total(iter_):
    return float(sum(t.value for t in iter_))


class PieSection:

    def __init__(self, label, fn):
        self.label = label
        self.fn = fn
        self.transactions = []
        self.next = None

    def add(self, transaction):
        if self.fn(transaction):
            self.transactions.append(transaction)
            return

        if self.next is not None:
            self.next.add(transaction)

    def total(self):
        return _total(self.transactions)

    def printLL(self):
        print(self.label +
              str([(t.value, t.categories[0].__class__.__name__)
                   for t in self.transactions]))
        if(self.next):
            self.next.printLL()


def section_factory(categories):

    def section(label, fn=None):
        if fn is None:
            def fn(t):
                return t.matches_category(
                    categories.category(label)
                )
        return PieSection(label, fn)

    return section


def anything_else(label="Anything else"):
    return PieSection(label, lambda _: True)


class PieChart:
    def __init__(self, *sections):
        self._sections = sections
        self._make_linked_list()
        self._head = sections[0]

    def add_transaction(self, trans):
        self._head.add(trans)

    def add_transactions(self, it):
        for trans in it:
            self.add_transaction(trans)

    def _make_linked_list(self):
        sections = self._sections
        sect = sections[0]

        for s in sections[1:]:
            sect.next = s
            sect = s

    def as_data_frame(self):
        labels = [sc.label for sc in self._sections]
        values = [sc.total() for sc in self._sections]
        return pd.DataFrame(
            {"values": values, "labels": labels},
            index=labels)

    def add_records(self, records):
        for trans in records:
            self.add_transaction(trans)

    def sections(self):
        return {
            section.label: section
            for section in self._sections
        }
