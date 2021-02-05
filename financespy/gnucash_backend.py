import gnucash
from gnucash import GncNumeric, Split
from financespy.categories import Category
from financespy.categories import Categories
from financespy.transaction import Transaction
from datetime import datetime
from financespy.memory_backend import month_iterator_from_query


from gnucash import \
    QOF_QUERY_AND, \
    QOF_QUERY_OR, \
    QOF_QUERY_NAND, \
    QOF_QUERY_NOR, \
    QOF_QUERY_XOR


from gnucash import \
    QOF_STRING_MATCH_NORMAL, \
    QOF_STRING_MATCH_CASEINSENSITIVE


from gnucash import \
    QOF_COMPARE_LT, \
    QOF_COMPARE_LTE, \
    QOF_COMPARE_EQUAL, \
    QOF_COMPARE_GT, \
    QOF_COMPARE_GTE, \
    QOF_COMPARE_NEQ

# These constants come from enums from C implementation
# see https://code.gnucash.org/docs/MAINT/group__Query.html
# (please report if link is broken)

SPLIT_TRANS = 'trans'
TRANS_DATE_POSTED = 'date-posted'
QOF_DATE_MATCH_NORMAL = 1
QOF_DATE_MATCH_DAY = 2
QOF_GUID_MATCH_NORMAL = 1
PARAM_LIST = [SPLIT_TRANS, TRANS_DATE_POSTED]
SPLIT_ACCOUNT = 'account'
QOF_PARAM_GUID = 'guid'

gnucash.gnucash_core.Account.__getitem__ = \
    lambda self, a: self.lookup_by_name(a)


def categories_from(account):
    '''Create a financespy.Categories object from a Gnucash root account'''

    categories_map = {}

    def _categories_from_dfs(account, parent):
        for child in account.get_children():
            category = Category(child.name, parent)
            category._account = child
            categories_map[child.name] = category
            _categories_from_dfs(child, category)

    root = Category(account.name, None)
    root._account = account
    categories_map[account.name] = root
    _categories_from_dfs(account, root)

    return Categories(categories_map, root)


def split_to_transaction(split, categories):
    transaction = split.GetParent()
    split = split.GetOtherSplit()
    # TODO - create Money implementation based on gnucash's
    # GncNumeric or Python's Fraction
    value = split.GetValue().to_double()
    category = categories.category(split.GetAccount().name)
    description = transaction.GetDescription()

    result = Transaction(
        value=value,
        categories=[category],
        description=description
    )
    result.date = transaction.GetDate().date()
    return result


def _insert_transaction(session, record, currency,
                        rec_date, account_to, account_from):
    book = session.book

    # set currency
    comm_table = book.get_table()
    currency = comm_table.lookup("CURRENCY", currency)

    transaction = gnucash.Transaction(book)
    transaction.BeginEdit()

    split_to = Split(book)
    # TODO - create money representation based on fractions
    value = GncNumeric(record.value.cents(), 100)
    split_to.SetValue(value)
    split_to.SetAccount(account_to)
    split_to.SetParent(transaction)

    split_from = Split(book)
    split_from.SetValue(value.neg())
    split_from.SetAccount(account_from)
    split_from.SetParent(transaction)

    # set transaction values
    transaction.SetDate(rec_date.day, rec_date.month, rec_date.year)
    transaction.SetDescription(record.description)
    transaction.SetCurrency(currency)
    transaction.CommitEdit()


class GnucashBackend:
    '''Implements a financespy backend class that uses a gnucash file as storage

    A GnucashBackend object is bounded to a Gnucash session and a specific
    account from the book. This account should be some child from "Assets",
    in order to match the account concept in FinancesPy. In Gnucash, everything
    can be an account, by the other hand, only cash in wallet, checking
    account, savings account, etc. are considered accounts in FinancesPy.
    Expenses accounts from gnucash (books, groceries, etc.) are mapped to
    FinancesPy categories.
    '''

    def __init__(self, session, account, categories, currency):
        self._session = session
        self._root_account = self._session.book.get_root_account()
        self._account = account
        self.categories = categories
        self._currency = currency

    def insert_record(self, date, record):
        expense_account = record.main_category()._account
        account_from = self._account
        session = self._session

        _insert_transaction(
            session=session,
            record=record,
            currency=self._currency,
            rec_date=date,
            account_to=expense_account,
            account_from=account_from
        )

    def day(self, day, month, year):
        dt = datetime(day=day, month=month, year=year)

        return self._query(date=dt)

    def month(self, month, year):
        def query(firstday, lastday):
            return self._query(
                date_from=firstday,
                date_to=lastday
            )
        return month_iterator_from_query(month, year, self, query)

    def _query(self, date=None, date_from=None, date_to=None, filters=[]):
        book = self._session.book
        query = gnucash.Query()
        query.search_for('Split')
        query.set_book(book)
        account_guid = self._account.GetGUID()

        query.add_guid_match(
            [SPLIT_ACCOUNT, QOF_PARAM_GUID], account_guid, QOF_QUERY_AND)

        if date:
            pred_data = gnucash.gnucash_core.QueryDatePredicate(
                QOF_COMPARE_EQUAL,
                QOF_DATE_MATCH_DAY,
                date)
            query.add_term(PARAM_LIST, pred_data, QOF_QUERY_AND)
        else:
            if date_from:
                pred_data = gnucash.gnucash_core.QueryDatePredicate(
                    QOF_COMPARE_GTE,
                    QOF_DATE_MATCH_NORMAL, date_from)
                query.add_term(PARAM_LIST, pred_data, QOF_QUERY_AND)

            if date_to:
                pred_data = gnucash.gnucash_core.QueryDatePredicate(
                    QOF_COMPARE_LTE,
                    QOF_DATE_MATCH_NORMAL, date_to)
                query.add_term(PARAM_LIST, pred_data, QOF_QUERY_AND)

        return (
            split_to_transaction(Split(instance=split), self.categories)
            for split in query.run()
        )
