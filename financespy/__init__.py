"""FinancesPy: A Python API for personal finance management.

A literate API for personal finance concepts inspired by GnuCash, Mint, and YNAB.
Provides support for multiple storage backends and hierarchical transaction categorization.
"""

from __future__ import annotations

# Core classes
from financespy.account import Account
from financespy.backend import Backend, CompositeBackend

# Backend implementations
from financespy.backends.filesystem_backend import FilesystemBackend
from financespy.backends.memory_backend import MemoryBackend
from financespy.backends.sql_backend import SQLBackend
from financespy.backends.xlsx_backend import XLSXBackend
from financespy.categories import Categories, Category

# Charting and visualization
from financespy.charting import PieChart, PieSection, section_factory

# Exceptions
from financespy.exceptions import (
    BackendConnectionError,
    BackendError,
    CategoryNotFoundError,
    CurrencyNotFoundError,
    DataValidationError,
    FinancesPyError,
    InvalidAmountError,
    ParseTransactionError,
)
from financespy.money import Currencies, Currency, Money

# Predicate compiler
from financespy.predicate_compiler import (
    PredicateCompilationError,
    PredicateCompiler,
    compile_predicate,
)

# Time utilities
from financespy.time_factory import parse_month
from financespy.transaction import Transaction

# Optional GnuCash support
try:
    from financespy.backends.gnucash_backend import (
        GnucashBackend,
        categories_from,
    )
except ImportError:
    # GnuCash dependencies not available
    GnucashBackend = None  # type: ignore
    categories_from = None  # type: ignore

__version__ = "0.1.0"
__author__ = "Danilo Mendonça Oliveira"
__email__ = "danilomendoncaoliveira@gmail.com"

__all__ = [
    # Core classes
    "Account",
    "Money",
    "Currency",
    "Currencies",
    "Transaction",
    "Category",
    "Categories",
    # Backend classes
    "Backend",
    "CompositeBackend",
    "FilesystemBackend",
    "MemoryBackend",
    "SQLBackend",
    "XLSXBackend",
    "GnucashBackend",
    # Charting
    "PieChart",
    "PieSection",
    "section_factory",
    # Utilities
    "parse_month",
    "categories_from",
    # Predicate compiler
    "PredicateCompiler",
    "compile_predicate",
    # Exceptions
    "PredicateCompilationError",
    "FinancesPyError",
    "ParseTransactionError",
    "CategoryNotFoundError",
    "CurrencyNotFoundError",
    "BackendError",
    "BackendConnectionError",
    "DataValidationError",
    "InvalidAmountError",
]
