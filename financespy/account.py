import datetime
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional

from financespy.backend import Backend
from financespy.backends.filesystem_backend import FilesystemBackend
from financespy.backends.memory_backend import MemoryBackend
from financespy.backends.xlsx_backend import XLSXBackend
from financespy.categories import Categories, categories_from_list
from financespy.transaction import Transaction

_current_year = datetime.datetime.now().year


class OpenAccountError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


def open_account(account_path: str) -> Optional["Account"]:
    """
    Creates an Account object from a given operating system path.
    The path can point to any supported storage: csv files, Excel spreadsheets,
    gnucash file, etc. Account metadata file stored as JSON is expected to be present,
    otherwise the method will throw an exception.

    Please read the documentation for understanding the organization
    of files for each backend type and account metadata.
    """

    if account_path is None:
        raise ValueError("account_path cannot be None")

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


def memory_account(categories: Any) -> "Account":
    meta = AccountMetadata(
        categories=categories,
        currency="eur",
        properties={},
        name="memory_account",
        backend_type="memory",
    )

    return Account(backend=MemoryBackend(categories), account_metadata=meta)


def open_folder(account_path: str) -> "Account":
    account_json = Path(account_path) / "account.json"

    if not account_json.exists():
        raise OpenAccountError(
            f"account.json file not found at folder [{account_json}]"
        )

    account_metadata = read_metadata(account_json)

    if not account_metadata.backend_type:
        raise OpenAccountError(
            "Account backend type not specified in account.json file"
        )

    backend: Optional[Backend] = None

    if account_metadata.backend_type == "xlsx":
        backend = XLSXBackend(account_path, account_metadata.categories)
    elif account_metadata.backend_type == "csv":
        backend = FilesystemBackend(account_path, account_metadata.categories)
    elif account_metadata.backend_type == "combined":
        from financespy.backends.combined_backend import CombinedBackend

        # Read full config for combined backend
        with open(account_json) as f:
            config = json.load(f)

        backend = CombinedBackend(
            Path(account_path), account_metadata.categories, config
        )

    if backend is None:
        raise OpenAccountError(
            f"Account backend type [{account_metadata.backend_type}] not supported"
        )

    return Account(backend, account_metadata)


def read_metadata(account_json: Path) -> "AccountMetadata":
    with open(account_json) as f:
        source_dict = json.load(f)
        name = source_dict.get("name", "")
        backend_type = source_dict.get("type", "")
        categories_raw = source_dict.get("categories", [])
        currency = source_dict.get("currency", "")
        properties = source_dict.get("properties", {})

        # Check if categories is a path reference to external file
        if isinstance(categories_raw, str):
            categories_list = _load_categories_from_file(account_json, categories_raw)
        else:
            categories_list = categories_raw

        return AccountMetadata(
            name=name,
            backend_type=backend_type,
            categories=categories_from_list(categories_list),
            currency=currency,
            properties=properties,
        )


def _load_categories_from_file(account_json: Path, categories_path: str) -> list[Any]:
    """
    Load categories from an external JSON file.

    Args:
        account_json: Path to the account.json file
        categories_path: Path to categories file (relative or absolute)

    Returns:
        List of categories loaded from the JSON file

    Raises:
        OpenAccountError: If file not found or invalid JSON
    """
    # Resolve path relative to account.json's parent directory
    categories_file = Path(categories_path)
    if not categories_file.is_absolute():
        # Relative path: resolve from account.json's directory
        categories_file = (account_json.parent / categories_path).resolve()

    # Load and parse the JSON file
    try:
        with open(categories_file) as f:
            categories_data = json.load(f)

            # Validate that the loaded data is a list
            if not isinstance(categories_data, list):
                raise OpenAccountError(
                    f"Categories file {categories_file} must contain a JSON array"
                )

            return categories_data

    except FileNotFoundError as e:
        raise OpenAccountError(f"Categories file not found: {categories_file}") from e
    except json.JSONDecodeError as e:
        raise OpenAccountError(
            f"Invalid JSON in categories file {categories_file}: {e}"
        ) from e
    except Exception as e:
        raise OpenAccountError(
            f"Error loading categories from {categories_file}: {e}"
        ) from e


def open_gnucash(gnucash_file: str) -> "Account":
    from gnucash import Session  # type: ignore[import-not-found]

    from financespy.backends import gnucash_backend
    from financespy.backends.gnucash_backend import GnucashBackend

    path = Path(gnucash_file)
    metadata_file = re.sub("[.]gnucash$", ".json", path.name)
    metadata = read_metadata(path.parent / metadata_file)

    session = Session(gnucash_file)

    gnucash_account = gnucash_backend.account_for(
        session, metadata.properties["account_backend"]
    )

    if not metadata.categories._categories:
        metadata.categories = gnucash_backend.categories_from(
            session, metadata.properties["account_categories"]
        )

    backend = GnucashBackend(
        session=session,
        account=gnucash_account,
        categories=metadata.categories,
        currency=metadata.currency,
    )

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
    properties: dict[str, Any]


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

    def __init__(self, backend: Backend, account_metadata: AccountMetadata) -> None:
        self.backend = backend
        self.metadata = account_metadata
        self.categories = account_metadata.categories

    def transactions(self, date_from: date, date_to: date) -> Iterator[Transaction]:
        #
        # if a backend-specific implementation exists, we use it.
        # It can be more efficient than our default implementation
        try:
            return self.backend.transactions(date_from, date_to)  # type: ignore[attr-defined,no-any-return]
        except AttributeError:
            pass

        return transactions_per_range(self.backend, date_from, date_to)

    def day(self, day: int, month: int, year: int = _current_year) -> Any:
        """
        Give all transactions for a specific day. If the year parameter, is not supplied
        it will use current year (as given by the operating system).
        """

        return self.backend.day(day, month, year)

    def month(self, month: int, year: int = _current_year) -> Any:
        """
        Give all transactions for a specific month. If the year parameter, is not supplied
        it will use current year (as given by the operating system).
        """

        return self.backend.month(month, year)

    def records(self, date_: date) -> Iterator[Transaction]:
        """
        Give all transactions for a specific date object. This can be any object that has the following attributes:
        year, day and month. Usually it should be a datetime.date object, but a duck-typed object also can be used.
        """

        return self.backend.records(date_)

    def insert_record(self, date_: date, transaction: Transaction) -> Optional[str]:
        """
        Insert a financial transaction at a specific date. Only the day/month/year values are important, the specific hour/minute
        are not considered.
        """

        return self.backend.insert_record(date_, transaction)

    def copy_year(
        self,
        account: "Account",
        year: int,
        tags: Optional[list[str]] = None,
        filters: Optional[list[Any]] = None,
    ) -> None:
        """Copies all transactions for an entire year from a source account
        to the current account. The tags parameter can be used to apply a special tag
        that can identify the transactions added by this methods. The filters parameter
        can exclude all transactions that matches at least one filter from the list"""
        if tags is None:
            tags = []
        if filters is None:
            filters = []

        for month in range(1, 13):
            transactions = filtered_records(
                account.month(month, year=year).records(), filters
            )

            for trans in transactions:
                for t in tags:
                    cat = self.categories.category(t)
                    trans.add_category(cat)

                if trans.date is not None:
                    self.insert_record(trans.date, trans)

    def update_record(self, transaction: Transaction) -> None:
        self.backend.edit_record(transaction)  # type: ignore[attr-defined]

    def delete_record(self, id: Any) -> None:
        self.backend.delete_record(id)  # type: ignore[attr-defined]


def filtered_records(
    records_it: Iterator[Transaction], filters: list[Any]
) -> Iterator[Transaction]:
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


def transactions_per_range(
    backend: Backend, date_from: date, date_to: date
) -> Iterator[Transaction]:
    year_from = date_from.year
    year_to = date_to.year

    def iterator() -> Iterator[Transaction]:
        for year in range(year_from, year_to + 1):
            for month in range(1, 13):
                for transaction in backend.month(year=year, month=month).records():
                    dt = transaction.date

                    if dt < date_from or dt > date_to:
                        continue

                    yield transaction

    return iterator()
