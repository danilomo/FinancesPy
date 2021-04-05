import datetime
import os
from pathlib import Path
import json
import re
from dataclasses import dataclass
from financespy import gnucash_backend
from financespy.gnucash_backend import GnucashBackend
from financespy.xlsx_backend import XLSXBackend
from financespy.filesystem_backend import FilesystemBackend
from financespy.categories import Categories
from financespy.categories import categories_from_list


_current_year = datetime.datetime.now().year

class OpenAccountError(Exception):
    
    def __init__(self, message):
        self.message = message

def open_account(account_path = None):
    if account_path is None:
        return open_default_account()

    if os.path.isdir(account_path):
        return open_folder(account_path)

    # we only support gnucash files
    extension = None
    
    try:
        dot_index = account_path.rindex(".")
        extension = account_path[-(len(account_path)-dot_index):]
    except ValueError as err:
        pass

    if extension == ".gnucash":
        return open_gnucash(account_path)

    raise OpenAccountError(f"File [{account_path}] is not a valid Gnucash file")



def open_folder(account_path):
    account_json = Path(account_path) / "account.json"

    if not account_json.exists():
        raise OpenAccountError(f"account.json file not found at folder [{account_json}]")

    account_metadata = read_metadata(account_json)    

    if not account_metadata.backend_type:
        raise OpenAccountError(f"Account backend type not specified in account.json file")

    backend = None
    
    if account_metadata.backend_type == "xlsx":
        backend = XLSXBackend(account_path)
    elif account_metadata.backend_type == "csv":
        backend = FilesystemBackend(account_path)

    if backend is None:
        raise OpenAccountError(f"Account backend type [{account_metadata.type} not supported]")

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
            properties=properties
        )


def open_gnucash(gnucash_file):
    from gnucash import Session
    
    path = Path(gnucash_file)
    metadata_file = re.sub('[.]gnucash$', ".json", path.name)
    metadata = read_metadata(str(path.parent / metadata_file))

    session = Session(gnucash_file)
    
    gnucash_account = gnucash_backend.account_for(
        session,
        metadata.properties['account_backend']
    )

    if not metadata.categories:
        metadata.categories = gnucash_backend.categories_from(
            session,
            metadata.properties['account_categories']
        )

    backend = GnucashBackend(
        session=session,
        account=gnucash_account
    )

    return Account(
        backend,
        metadata
    )


@dataclass
class AccountMetadata:
    name: str
    backend_type: str
    currency: str
    categories: Categories
    properties: dict


class Account:
    def __init__(self, backend, account_metadata):
        backend.categories = account_metadata.categories
        backend.currency = account_metadata.currency
        
        self.backend = backend
        self.metadata = account_metadata
        

    def day(self, day, month, year=_current_year):
        return self.backend.day(day, month, year)

    def month(self, month, year=_current_year):
        return self.backend.month(month, year)

    def records(self, date):
        return self.backend.records(date)

    def insert_record(self, date, transaction):
        self.backend.insert_record(date, transaction)

    def copy_year(self, account, year, tags=[], filters=[]):
        for month in range(1, 13):
            for trans in account.month(month, year=year).records():
                matches_some_filter = False

                for f in filters:
                    if trans.matches_category(f):
                        matches_some_filter = True
                        break

                if matches_some_filter:
                    continue

                for t in tags:
                    cat = self._backend.category_from(t)
                    trans.add_category(cat)

                self.insert_record(trans.date, trans)
