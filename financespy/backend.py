"""Abstract backend interface and composite backend implementation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import date
from typing import TYPE_CHECKING, Any, Callable

from financespy.categories import Categories
from financespy.exceptions import BackendError, DataValidationError

if TYPE_CHECKING:
    from financespy.transaction import Transaction


def _satisfy_filters(record: Any, filters: list[Callable[[Any], bool]]) -> bool:
    if not filters:
        return True

    try:
        num_filters = len(filters)
        test_all = (f(record) for f in filters)
        return num_filters == sum(test_all)
    except Exception as e:
        logging.error(f"Filter validation failed for record {record}: {e}")
        raise DataValidationError(f"Filter validation failed: {e}") from e


class Backend(ABC):
    """Abstract base class for all storage backends.

    Provides the interface that all backend implementations must follow,
    including methods for storing and retrieving financial data.

    Args:
        categories: Category system for transaction categorization

    Raises:
        DataValidationError: If categories is None
    """

    def __init__(self, categories: Categories) -> None:
        """Initialize the backend.

        Raises:
            BackendError: If backend initialization fails
        """
        if categories is None:
            raise DataValidationError("Categories system is required")

        self.categories = categories
        try:
            # Import here to avoid circular imports
            import financespy.time_factory as time_factory

            self._timef = time_factory.TimeFactory(self)
            self._logger = logging.getLogger(self.__class__.__name__)
        except Exception as e:
            raise BackendError(f"Failed to initialize backend: {e}") from e

    def day(self, day: int, month: int, year: int) -> Any:
        """Get a day iterator for the specified date.

        Args:
            day: Day of month (1-31)
            month: Month number (1-12)
            year: Year

        Returns:
            Day iterator object

        Raises:
            DataValidationError: If date parameters are invalid
            BackendError: If backend operation fails
        """
        self._validate_date_params(day, month, year)
        try:
            return self._timef.month(month, year).day(day)
        except Exception as e:
            self._logger.error(
                f"Failed to get day iterator for {year}-{month}-{day}: {e}"
            )
            raise BackendError(f"Failed to get day iterator: {e}") from e

    def month(self, month: int, year: int) -> Any:
        """Get a month iterator for the specified month.

        Args:
            month: Month number (1-12)
            year: Year

        Returns:
            Month iterator object

        Raises:
            DataValidationError: If date parameters are invalid
            BackendError: If backend operation fails
        """
        self._validate_month_year(month, year)
        try:
            return self._timef.month(month, year)
        except Exception as e:
            self._logger.error(f"Failed to get month iterator for {year}-{month}: {e}")
            raise BackendError(f"Failed to get month iterator: {e}") from e

    def copy_from(
        self,
        backend: Backend,
        year: int,
        filters: list[Callable[[Any], bool]] | None = None,
    ) -> None:
        """Copy data from another backend for a specific year.

        Args:
            backend: Source backend to copy from
            year: Year to copy
            filters: Optional list of filter functions

        Raises:
            DataValidationError: If validation fails
            BackendError: If copy operation fails
        """
        if not isinstance(backend, Backend):
            raise DataValidationError("Source must be a Backend instance")

        if not isinstance(year, int) or year < 1900 or year > 2100:
            raise DataValidationError(f"Invalid year: {year}")

        if filters is None:
            filters = []

        self._logger.info(
            f"Starting copy from {backend.__class__.__name__} for year {year}"
        )

        try:
            copied_count = 0
            for month in range(1, 13):
                month_iterator = backend.month(month, year)

                for record in month_iterator.records():
                    if _satisfy_filters(record, filters):
                        self.insert_record(record.date, record)
                        copied_count += 1

            self._logger.info(
                f"Successfully copied {copied_count} records for year {year}"
            )
        except Exception as e:
            self._logger.error(f"Failed to copy data from backend: {e}")
            raise BackendError(f"Copy operation failed: {e}") from e

    @abstractmethod
    def insert_record(self, date: date, transaction: Transaction) -> str | None:
        """Insert a transaction record.

        Args:
            date: Transaction date
            transaction: Transaction to insert

        Returns:
            Optional transaction ID if supported by backend

        Raises:
            DataValidationError: If input validation fails
            BackendError: If insert operation fails
        """
        pass

    @abstractmethod
    def records(self, date: date) -> Iterator[Transaction]:
        """Get all records for a specific date.

        Args:
            date: Date to query

        Returns:
            Iterator of transactions for the date

        Raises:
            BackendError: If query fails
        """
        pass

    def _validate_date_params(self, day: int, month: int, year: int) -> None:
        if not isinstance(day, int) or day < 1 or day > 31:
            raise DataValidationError(f"Invalid day: {day}")
        if not isinstance(month, int) or month < 1 or month > 12:
            raise DataValidationError(f"Invalid month: {month}")
        if not isinstance(year, int) or year < 1900 or year > 2100:
            raise DataValidationError(f"Invalid year: {year}")

    def _validate_month_year(self, month: int, year: int) -> None:
        if not isinstance(month, int) or month < 1 or month > 12:
            raise DataValidationError(f"Invalid month: {month}")
        if not isinstance(year, int) or year < 1900 or year > 2100:
            raise DataValidationError(f"Invalid year: {year}")

    def __enter__(self) -> Backend:
        """Context manager entry."""
        return self

    @abstractmethod
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit."""
        pass


class CompositeBackend:
    """Composite backend that separates read and write operations.

    Allows using different backends for reading and writing,
    useful for scenarios like reading from a database and writing to files.
    """

    def __init__(self, readbe: Backend, writebe: Backend) -> None:
        """Initialize composite backend.

        Args:
            readbe: Backend to use for read operations
            writebe: Backend to use for write operations

        Raises:
            DataValidationError: If backends are invalid
        """
        if not isinstance(readbe, Backend):
            raise DataValidationError("Read backend must be a Backend instance")
        if not isinstance(writebe, Backend):
            raise DataValidationError("Write backend must be a Backend instance")

        self._readbe = readbe
        self._writebe = writebe
        self._logger = logging.getLogger(self.__class__.__name__)

    def day(self, day: int, month: int, year: int) -> Any:
        """Get day iterator from read backend."""
        return self._readbe.day(day, month, year)

    def month(self, month: int, year: int) -> Any:
        """Get month iterator from read backend."""
        return self._readbe.month(month, year)

    def insert_record(self, date: date, transaction: Transaction) -> str | None:
        """Insert record using write backend.

        Args:
            date: Transaction date
            transaction: Transaction to insert

        Returns:
            Optional transaction ID if supported by backend

        Raises:
            DataValidationError: If input validation fails
            BackendError: If insert operation fails
        """
        try:
            return self._writebe.insert_record(date, transaction)
        except Exception as e:
            self._logger.error(f"Failed to insert record via write backend: {e}")
            raise

    def __enter__(self) -> CompositeBackend:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit."""
        pass
