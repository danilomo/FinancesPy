import datetime
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from financespy.categories import Categories, categories_from_list
from financespy.backends.filesystem_backend import FilesystemBackend
from financespy.backends.memory_backend import MemoryBackend
from financespy.backends.xlsx_backend import XLSXBackend

_current_year = datetime.datetime.now().year


class OpenAccountError(Exception):
    def __init__(self, message):
        self.message = message


def open_account(account_path=None):
    """
    Creates an Account object from a given operating system path.
    The path can point to any supported storage: csv files, Excel spreadsheets,
    gnucash file, etc. Account metadata file stored as JSON is expected to be present,
    otherwise the method will throw an exception.

    Please read the documentation for understanding the organization
    of files for each backend type and account metadata.
    """

    if account_path is None:
        # return open_default_account()
        # TODO implement default account
        pass

    if os.path.isdir(account_path):
        return open_folder(account_path)

    # we only support gnucash files
    extension = None

    try:
        dot_index = account_path.rindex(".")
        extension = account_path[-(len(account_path) - dot_index) :]
    except ValueError:
        pass

    if extension == ".gnucash":
        return open_gnucash(account_path)

    raise OpenAccountError(f"File [{account_path}] is not a valid Gnucash file")


def memory_account(categories):
    meta = AccountMetadata(
        categories=categories,
        currency="eur",
        properties={},
        name="memory_account",
        backend_type="memory",
    )

    return Account(backend=MemoryBackend(categories), account_metadata=meta)


def open_folder(account_path):
    account_json = Path(account_path) / "account.json"

    if not account_json.exists():
        raise OpenAccountError(
            f"account.json file not found at folder [{account_json}]"
        )

    account_metadata = read_metadata(account_json)

    if not account_metadata.backend_type:
        raise OpenAccountError(
            f"Account backend type not specified in account.json file"
        )

    backend = None

    if account_metadata.backend_type == "xlsx":
        backend = XLSXBackend(account_path)
    elif account_metadata.backend_type == "csv":
        backend = FilesystemBackend(account_path)

    if backend is None:
        raise OpenAccountError(
            f"Account backend type [{account_metadata.type} not supported]"
        )

    return Account(backend, account_metadata)


def read_metadata(account_json):
    with open(account_json) as f:
        source_dict = json.load(f)
        name = source_dict.get("name", "")
        backend_type = source_dict.get("type", "")
        categories = source_dict.get("categories", [])
        currency = source_dict.get("currency", "")
        properties = source_dict.get("properties", {})

        return AccountMetadata(
            name=name,
            backend_type=backend_type,
            categories=categories_from_list(categories),
            currency=currency,
            properties=properties,
        )


def open_gnucash(gnucash_file):
    from gnucash import Session

    from financespy import gnucash_backend
    from financespy.backends.gnucash_backend import GnucashBackend

    path = Path(gnucash_file)
    metadata_file = re.sub("[.]gnucash$", ".json", path.name)
    metadata = read_metadata(str(path.parent / metadata_file))

    session = Session(gnucash_file)

    gnucash_account = gnucash_backend.account_for(
        session, metadata.properties["account_backend"]
    )

    if not metadata.categories:
        metadata.categories = gnucash_backend.categories_from(
            session, metadata.properties["account_categories"]
        )

    backend = GnucashBackend(session=session, account=gnucash_account)

    return Account(backend, metadata)


@dataclass
class AccountMetadata:
    """
    Describes the properties of the account.
    """

    name: str
    backend_type: str
    currency: str
    categories: Categories
    properties: dict


class Account:
    """
    Provides access to a collection of financial transaction
    stored in some medium (gnucash file, relational database,
    Excel spreadsheet, etc.). It exports query methods for retrieving
    transactions for a given time interval (a day, a month, a year, etc.),
    and also a method for updating the storage (if supported).

    This class just delegates the operations to the specific backend
    that is given on the constructor. However, the usage of this
    class should be encouraged in conjunction with the "open_account"
    function that is able to create an account object
    with the correcty backend and metadata already configured.
    """

    def __init__(self, backend, account_metadata):
        backend.categories = account_metadata.categories
        backend.currency = account_metadata.currency

        self.backend = backend
        self.metadata = account_metadata
        self.categories = account_metadata.categories

    def transactions(self, date_from, date_to):
        # TODO - if date_from > date_to - throw error
        #
        # if a backend-specific implementation exists, we use it.
        # It can be more efficient than our default implementation
        try:
            return self.backend.transactions(date_from, date_to)
        except AttributeError:
            pass

        return transactions_per_range(self.backend, date_from, date_to)

    def day(self, day, month, year=_current_year):
        """
        Give all transactions for a specific day. If the year parameter, is not supplied
        it will use current year (as given by the operating system).
        """

        return self.backend.day(day, month, year)

    def month(self, month, year=_current_year):
        """
        Give all transactions for a specific month. If the year parameter, is not supplied
        it will use current year (as given by the operating system).
        """

        return self.backend.month(month, year)

    def records(self, date_):
        """
        Give all transactions for a specific date object. This can be any object that has the following attributes:
        year, day and month. Usually it should be a datetime.date object, but a duck-typed object also can be used.
        """

        return self.backend.records(date_)

    def insert_record(self, date_, transaction):
        """
        Insert a financial transaction at a specific date. Only the day/month/year values are important, the specific hour/minute
        are not considered.
        """

        self.backend.insert_record(date_, transaction)

    def copy_year(self, account, year, tags=[], filters=[]):
        """Copies all transactions for an entire year from a source account
        to the current account. The tags parameter can be used to apply a special tag
        that can identify the transactions added by this methods. The filters parameter
        can exclude all transactions that matches at least one filter from the list"""

        for month in range(1, 13):
            transactions = filtered_records(
                account.month(month, year=year).records(), filters
            )

            for trans in transactions:
                for t in tags:
                    cat = self.backend.category_from(t)
                    trans.add_category(cat)

                self.insert_record(trans.date, trans)


def filtered_records(records_it, filters):
    """Gives a filtered records iterator that contains only records
    that doesn't match *any* filter from the filter list"""

    for trans in records_it:
        matches_some_filter = False

        for f in filters:
            if trans.matches_category(f):
                matches_some_filter = True
                break

        if matches_some_filter:
            continue

        yield trans


def transactions_per_range(backend, date_from, date_to):
    year_from = date_from.year
    year_to = date_to.year

    def iterator():
        for year in range(year_from, year_to + 1):
            for month in range(1, 13):
                dt = date(year=year, month=month, day=1)

                for transaction in backend.month(year=year, month=month).records():
                    dt = transaction.date

                    if dt < date_from or dt > date_to:
                        continue

                    yield transaction

    return iterator()
