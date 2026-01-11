"""In-memory backend implementation for FinancesPy."""

import calendar
import collections
import logging
import uuid
from collections.abc import Iterator
from datetime import date as datetime_date
from datetime import datetime
from typing import Any, Callable, Optional, Union

from financespy.backend import Backend, CompositeBackend
from financespy.categories import Categories
from financespy.exceptions import BackendError, DataValidationError
from financespy.models import TransactionModel
from financespy.money import Money
from financespy.time_factory import parse_month
from financespy.transaction import Transaction, parse_transaction


class MemoryBackend(Backend):
    """In-memory storage backend for transactions.

    This backend stores all transactions in memory using nested dictionaries
    organized by year, month, and day. Suitable for testing and data transfer
    operations.
    """

    def __init__(self, categories: Categories) -> None:
        """
        Initialize memory backend.
        """
        super().__init__(categories)
        self._months: dict[tuple, list[list[Transaction]]] = collections.defaultdict(
            lambda: [[] for _ in range(0, 32)]
        )
        self._records_by_id: dict[str, Transaction] = {}
        self.categories = categories
        self._logger.info("MemoryBackend initialized")

    def insert_record(
        self, date: datetime_date, record: Union[Transaction, TransactionModel, str]
    ) -> str:
        """Insert a transaction record.

        Args:
            date: Transaction date
            record: Transaction to insert (Transaction, TransactionModel, or string)

        Returns:
            Generated transaction ID

        Raises:
            DataValidationError: If record validation fails
            BackendError: If insert operation fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        try:
            if isinstance(record, TransactionModel):
                record = Transaction.to_transaction(record, self.categories)
            elif isinstance(record, str):
                record = parse_transaction(record, self.categories)
            elif not isinstance(record, Transaction):
                raise DataValidationError(f"Unsupported record type: {type(record)}")

            # Generate unique ID
            record_id = str(uuid.uuid4())
            record.id = record_id

            # Store record
            self._records_by_id[record_id] = record
            self._months[(date.year, date.month)][date.day].append(record)

            self._logger.debug(f"Inserted record {record_id} for date {date}")
            return record_id

        except Exception as e:
            self._logger.error(f"Failed to insert record for date {date}: {e}")
            raise BackendError(f"Insert operation failed: {e}") from e

    def records(self, date: datetime_date) -> Iterator[Transaction]:
        """Get all records for a specific date.

        Args:
            date: Date to query

        Returns:
            Iterator of transactions for the date

        Raises:
            DataValidationError: If date is invalid
            BackendError: If query fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        try:
            return (
                record
                for record in self._months[(date.year, date.month)][date.day]
                if record.id in self._records_by_id
            )
        except Exception as e:
            self._logger.error(f"Failed to retrieve records for date {date}: {e}")
            raise BackendError(f"Query operation failed: {e}") from e

    def category_from(self, name: str) -> Any:
        """Get a category by name.

        Args:
            name: Category name

        Returns:
            Category object

        Raises:
            DataValidationError: If name is invalid
            BackendError: If category lookup fails
        """
        if not isinstance(name, str) or not name.strip():
            raise DataValidationError("Category name must be a non-empty string")

        try:
            return self.categories.category(name)
        except Exception as e:
            self._logger.error(f"Failed to get category '{name}': {e}")
            raise BackendError(f"Category lookup failed: {e}") from e

    def edit_record(self, record: Transaction) -> None:
        """Edit an existing transaction record.

        Args:
            record: Transaction with updated fields (must have valid ID)

        Raises:
            DataValidationError: If record validation fails
            BackendError: If edit operation fails
        """
        if not isinstance(record, Transaction):
            raise DataValidationError("Record must be a Transaction instance")

        if not hasattr(record, "id") or not record.id:
            raise DataValidationError("Record must have a valid ID")

        if record.id not in self._records_by_id:
            raise DataValidationError(f"Record with ID {record.id} not found")

        try:
            to_edit = self._records_by_id[record.id]

            # Update fields if provided
            if record.value is not None:
                to_edit.value = Money(value=record.value)

            if record.date and record.date != datetime(1970, 1, 1):
                to_edit.date = record.date

            if record.categories:
                to_edit.categories = record.categories

            if record.description:
                to_edit.description = record.description

            self._logger.debug(f"Edited record {record.id}")

        except Exception as e:
            self._logger.error(f"Failed to edit record {record.id}: {e}")
            raise BackendError(f"Edit operation failed: {e}") from e

    def delete_record(self, record_id: str) -> None:
        """Delete a transaction record.

        Args:
            record_id: ID of the record to delete

        Raises:
            DataValidationError: If record_id is invalid
            BackendError: If delete operation fails
        """
        if not isinstance(record_id, str) or not record_id.strip():
            raise DataValidationError("Record ID must be a non-empty string")

        if record_id not in self._records_by_id:
            raise DataValidationError(f"Record with ID {record_id} not found")

        try:
            del self._records_by_id[record_id]
            self._logger.debug(f"Deleted record {record_id}")
        except Exception as e:
            self._logger.error(f"Failed to delete record {record_id}: {e}")
            raise BackendError(f"Delete operation failed: {e}") from e

    def get_record_count(self) -> int:
        """Get total count of records in memory.

        Returns:
            Total number of records stored
        """
        return len(self._records_by_id)

    def clear_all(self) -> None:
        """Clear all records from memory.

        Warning:
            This operation cannot be undone.
        """
        self._months.clear()
        self._records_by_id.clear()
        self._logger.info("Cleared all records from memory")

    def get_record_by_id(self, record_id: str) -> Optional[Transaction]:
        """Get a specific record by ID.

        Args:
            record_id: ID of the record to retrieve

        Returns:
            Transaction if found, None otherwise

        Raises:
            DataValidationError: If record_id is invalid
        """
        if not isinstance(record_id, str) or not record_id.strip():
            raise DataValidationError("Record ID must be a non-empty string")

        return self._records_by_id.get(record_id)

    def month(self, month: int, year: int) -> Any:
        """Get month iterator for the specified month.

        Args:
            month: Month number (1-12) or month name string (e.g., 'sep', 'september')
            year: Year

        Returns:
            Month iterator object

        Raises:
            DataValidationError: If parameters are invalid
            BackendError: If backend operation fails
        """
        month_num = parse_month(month)
        self._validate_month_year(month_num, year)
        try:
            return self._timef.month(month_num, year)
        except Exception as e:
            self._logger.error(f"Failed to get month iterator for {year}-{month}: {e}")
            raise BackendError(f"Failed to get month iterator: {e}") from e

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            traceback: Exception traceback
        """
        pass


def month_iterator_from_query(
    month: int, year: int, backend: Backend, query: Callable
) -> Any:
    """Create a month iterator from a query function.

    Args:
        month: Month number (1-12)
        year: Year
        backend: Source backend
        query: Query function that takes (first_day, last_day) and returns transactions

    Returns:
        Month iterator for the queried data

    Raises:
        DataValidationError: If parameters are invalid
        BackendError: If query execution fails
    """
    if not isinstance(month, int) or month < 1 or month > 12:
        raise DataValidationError(f"Invalid month: {month}")
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise DataValidationError(f"Invalid year: {year}")
    if not callable(query):
        raise DataValidationError("Query must be callable")

    try:
        m = parse_month(month)
        firstday = datetime(day=1, month=m, year=year)

        # Fix: Calculate correct last day of month
        last_day_of_month = calendar.monthrange(year, m)[1]
        lastday = datetime(day=last_day_of_month, month=m, year=year)

        results = query(firstday, lastday)
        mb = MemoryBackend(backend.categories)

        for t in results:
            mb.insert_record(t.date, t)

        cb = CompositeBackend(mb, backend)
        return cb.month(month, year)

    except Exception as e:
        logging.error(f"Failed to create month iterator for {year}-{month}: {e}")
        raise BackendError(f"Month iterator creation failed: {e}") from e
