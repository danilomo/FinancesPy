"""Custom exceptions for the FinancesPy package."""

from __future__ import annotations


class FinancesPyError(Exception):
    """Base exception class for all FinancesPy errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ParseTransactionError(FinancesPyError):
    """Exception raised when parsing transaction data fails."""

    pass


class CategoryNotFoundError(FinancesPyError):
    """Exception raised when a requested category is not found."""

    pass


class CurrencyNotFoundError(FinancesPyError):
    """Exception raised when a requested currency is not found."""

    pass


class BackendError(FinancesPyError):
    """Base class for backend-related errors."""

    pass


class BackendConnectionError(BackendError):
    """Exception raised when backend connection fails."""

    pass


class DataValidationError(FinancesPyError):
    """Exception raised when data validation fails."""

    pass


class InvalidAmountError(FinancesPyError):
    """Exception raised when an invalid monetary amount is provided."""

    pass
