from openpyxl import load_workbook

from financespy.backend import Backend
from financespy.money import Money
import pathlib
from financespy.transaction import Transaction, parse_transaction
from datetime import datetime


def with_id(trans, id):
    trans.id = id
    return trans


class XLSXBackend(Backend):
    def __init__(self, folder):
        super().__init__()
        self.folder = pathlib.Path(folder)
        self._workbooks = {}

    def _filename(self, date):
        return self.folder / f"{str(date.year)}.xlsx"

    def _get_workbook(self, date):
        if date.year not in self._workbooks:
            workbook = load_workbook(filename=self._filename(date))
            self._workbooks[date.year] = workbook
            return workbook

        return self._workbooks[date.year]

    def _row_to_transaction(self, row):
        cat = lambda c: self.categories.category(c)
        categories = [
            cat(c) for c in (
                cat.strip() for cat in row[1].value.split(",")
            )
        ]
        return Transaction(
            value=Money(row[2].value),
            categories=categories,
            description=row[3].value
        )

    def _rows_to_records(self, rows, date):
        return (
            with_id(
                self._row_to_transaction(row),
                f"{date}_{index}",
            )
            for row, index in list(rows)[1:]
            if row[0].value and date.day == int(row[0].value)
        )

    def records(self, date):
        workbook = self._get_workbook(date)
        rows = list(workbook.worksheets[date.month - 1].rows)
        rows = zip(rows, range(0, len(rows)))
        return self._rows_to_records(rows, date)

    def insert_record(self, date, transaction):
        if type(transaction) is not Transaction:
            raise TypeError("Supplied parameter is not a transaction")

        workbook = self._get_workbook(date)
        sheet = workbook.worksheets[date.month - 1]
        sheet.append(
            [
                date.day,
                str(transaction.main_category()),
                str(transaction.value),
                transaction.description,
            ]
        )
        sheet_copy = [[c.value for c in r] for r in sheet][1:]
        sheet_copy.sort(key=lambda row: row[0])

        for i in range(0, len(sheet_copy)):
            for j in range(0, len(sheet_copy[i])):
                sheet.cell(i + 2, j + 1).value = sheet_copy[i][j]

        workbook.save(self._filename(date))

    def edit_record(self, transaction):
        date_str, pos_str = transaction.id.split("_")

        date = datetime.strptime(date_str, "%Y-%m-%d")

        if transaction.date != date:
            self._edit_record_with_new_date(transaction)

        workbook = self._get_workbook(date)
        sheet = workbook.worksheets[date.month - 1]

        pos = int(pos_str) + 1 # plus one to skip header

        if transaction.categories:
            sheet.cell(row=pos, column=2).value = ", ".join(str(cat) for cat in transaction.categories)

        if transaction.value:
            sheet.cell(row=pos, column=3).value = str(transaction.value)

        if transaction.description:
            sheet.cell(row=pos, column=4).value = transaction.description

        workbook.save(self._filename(date))

    def _edit_record_with_new_date(self, transaction):
        self.delete_record(transaction.id)
        self.insert_record(transaction.date, transaction)

    def delete_record(self, id):
        date_str, pos_str = id.split("_")
        date = datetime.strptime(date_str, "%Y-%m-%d")
        pos = int(pos_str) + 1

        workbook = self._get_workbook(date)
        sheet = workbook.worksheets[date.month - 1]

        sheet.delete_rows(pos)
        workbook.save(self._filename((date)))