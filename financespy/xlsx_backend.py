import openpyxl
from datetime import date
from openpyxl import load_workbook
from financespy.transaction import parse_transaction

_months = ['january', 'february', 'march', 'april', 'may', 'june', 'july',
          'august', 'september', 'october', 'november', 'december']

class XLSXBackend:
    def __init__(self, folder, categories):
        self.folder = folder
        self._workbooks = {}
        self._categories = categories

    def _init_workbook(self):
        self

    def _get_workbook(self, date):
        if date.month not in self._workbooks:
            workbook = load_workbook(
                filename = self.folder + "/"
                + _months[date.month-1]
                + ".xlsx"
            )
            self._workbooks[date.month] = workbook
            return workbook

        return self._workbooks[date.month]

    def _rows_to_records(self,rows):
        return (
            parse_transaction(
                str(row[1].value)
                + ","
                + str(row[0].value),
                self._categories
            )
            for row in rows            
        )

    def records(self, date):        
        workbook = self._get_workbook(date)

        return self._rows_to_records(
            workbook.worksheets[date.day-1].rows
        )
