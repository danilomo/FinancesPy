import os
from financespy.transaction import parse_transaction
from financespy.backend import Backend

_months = ["jan", "feb", "mar", "apr", "may", "jun",
           "jul", "aug", "sep", "oct", "nov", "dec"]


class FilesystemBackend(Backend):
    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def insert_record(self, date, record):
        with open(self.file(date), "+a") as f:
            f.write(str(record) + "\n")
            f.close()

    def records(self, date):
        if not os.path.exists(self.file(date)):
            return

        with open(self.file(date)) as f:
            for line in f:
                transaction = parse_transaction(line.strip())
                transaction.date = date
                yield transaction

    def file(self, date):
        return self.month_folder(date) + str(date.day) + ".csv"

    def month_folder(self, date):
        return self.folder + str(date.year) + "/" + _months[date.month-1] + "/"
