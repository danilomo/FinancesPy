from openpyxl import load_workbook
from financespy.transaction import parse_transaction
from financespy.transaction import Transaction
from financespy.backend import Backend


class XLSXBackend(Backend):
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
        self._workbooks = {}

    def _filename(self, date):
        return self.folder + "/" + str(date.year) + ".xlsx"

    def _get_workbook(self, date):
        if date.month not in self._workbooks:
            workbook = load_workbook(
                filename=self._filename(date)
            )
            self._workbooks[date.year] = workbook
            return workbook

        return self._workbooks[date.month]

    def _rows_to_records(self, rows, date):
        return (
            parse_transaction(
                str(row[2].value)
                + ","
                + str(row[1].value),
                self.categories
            )
            for row in list(rows)[1:]
            if row[0].value and date.day == int(row[0].value)
        )

    def records(self, date):
        workbook = self._get_workbook(date)

        return self._rows_to_records(
            workbook.worksheets[date.month-1].rows,
            date
        )

    def insert_record(self, date, transaction):
        if type(transaction) is not Transaction:
            raise TypeError("Supplied parameter is not a transaction")

        workbook = self._get_workbook(date)
        sheet = workbook.worksheets[date.month-1]

        sheet.append([
            date.day,
            str(transaction.main_category()),
            str(transaction.value)
        ])

        workbook.save(self._filename(date))
