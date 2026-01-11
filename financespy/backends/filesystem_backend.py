"""Filesystem-based backend implementation for FinancesPy."""

import pathlib
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from datetime import date as datetime_date
from io import TextIOWrapper
from typing import Optional, Union

from financespy.backend import Backend
from financespy.categories import Categories
from financespy.exceptions import (
    BackendConnectionError,
    BackendError,
    DataValidationError,
)
from financespy.time_factory import MONTHS_SHORT
from financespy.transaction import Transaction, parse_transaction


class FilesystemBackend(Backend):
    """Filesystem-based storage backend for transactions.

    Stores transactions in CSV files organized by year/month/day structure:
    - root_folder/YYYY/MMM/DD.csv

    Example structure:
    - 2023/jan/1.csv, 2.csv, etc.
    - 2023/feb/1.csv, 2.csv, etc.
    """

    def __init__(
        self, folder: Union[str, pathlib.Path], categories: Categories
    ) -> None:
        """Initialize filesystem backend.

        Args:
            folder: Root folder path for storing transaction files
            categories: Category system for transaction categorization

        Raises:
            DataValidationError: If folder path is invalid
            BackendConnectionError: If folder cannot be accessed or created
        """
        if not folder:
            raise DataValidationError("Folder path cannot be empty")

        super().__init__(categories)

        self.folder = pathlib.Path(folder)
        self.categories = categories

        try:
            # Ensure the root folder exists
            self.folder.mkdir(parents=True, exist_ok=True)

            test_file = self.folder / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except OSError as e:
                raise BackendConnectionError(
                    f"Cannot write to folder {folder}: {e}"
                ) from e

        except Exception as e:
            self._logger.error(f"Failed to initialize filesystem backend: {e}")
            raise BackendConnectionError(
                f"Filesystem backend initialization failed: {e}"
            ) from e

        self._logger.info(f"FilesystemBackend initialized with folder: {self.folder}")

    def insert_record(
        self, date: datetime_date, record: Union[Transaction, str]
    ) -> Optional[str]:
        """Insert a transaction record to the appropriate file.

        Args:
            date: Transaction date
            record: Transaction to insert

        Returns:
            None (filesystem backend doesn't support record IDs)

        Raises:
            DataValidationError: If input validation fails
            BackendError: If file operation fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        # Convert string to Transaction if needed
        if isinstance(record, str):
            if not self.categories:
                raise DataValidationError(
                    "Categories system required for string parsing"
                )
            record = parse_transaction(record, self.categories)
        elif not isinstance(record, Transaction):
            raise DataValidationError(
                f"Record must be Transaction or string, got {type(record)}"
            )

        try:
            file_path = self._get_file_path(date)
            self._ensure_directory_exists(file_path.parent)

            with self._safe_file_write(file_path) as f:
                f.write(str(record) + "\n")

            self._logger.debug(f"Inserted record to {file_path}")
            return None  # Filesystem backend doesn't support IDs

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
            BackendError: If file operation fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        try:
            file_path = self._get_file_path(date)

            if not file_path.exists():
                self._logger.debug(f"No file found for date {date}")
                return iter([])

            return self._read_transactions_from_file(file_path, date)

        except Exception as e:
            self._logger.error(f"Failed to retrieve records for date {date}: {e}")
            raise BackendError(f"Query operation failed: {e}") from e

    def _read_transactions_from_file(
        self, file_path: pathlib.Path, date: datetime_date
    ) -> Iterator[Transaction]:
        """Read transactions from a file.

        Args:
            file_path: Path to the transaction file
            date: Date to assign to transactions

        Yields:
            Transaction objects

        Raises:
            BackendError: If file reading fails
        """
        if not self.categories:
            raise BackendError("Categories system required for reading transactions")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    try:
                        transaction = parse_transaction(line, self.categories)
                        transaction.date = date
                        yield transaction
                    except Exception as e:
                        self._logger.warning(
                            f"Failed to parse line {line_num} in {file_path}: {e}"
                        )
                        continue  # Skip malformed lines

        except Exception as e:
            raise BackendError(f"Failed to read from {file_path}: {e}") from e

    def _get_file_path(self, date: datetime_date) -> pathlib.Path:
        month_folder = self._get_month_folder(date)
        return month_folder / f"{date.day}.csv"

    def _get_month_folder(self, date: datetime_date) -> pathlib.Path:
        return self.folder / str(date.year) / MONTHS_SHORT[date.month - 1]

    def _ensure_directory_exists(self, directory: pathlib.Path) -> None:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise BackendError(f"Failed to create directory {directory}: {e}") from e

    @contextmanager
    def _safe_file_write(
        self, file_path: pathlib.Path
    ) -> Generator[TextIOWrapper, None, None]:
        try:
            with file_path.open("a", encoding="utf-8") as f:
                yield f
        except Exception as e:
            raise BackendError(f"Failed to write to {file_path}: {e}") from e

    def get_available_dates(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> list[datetime_date]:
        """Get list of dates that have transaction data.

        Args:
            year: Optional year filter
            month: Optional month filter (requires year)

        Returns:
            List of dates with available data

        Raises:
            DataValidationError: If parameters are invalid
        """
        if month is not None and year is None:
            raise DataValidationError("Year must be specified when month is provided")

        try:
            if year is not None:
                return self._get_dates_for_year(year, month)
            else:
                return self._get_dates_for_all_years()

        except Exception as e:
            self._logger.error(f"Failed to get available dates: {e}")
            raise BackendError(f"Failed to get available dates: {e}") from e

    def _get_dates_for_year(
        self, year: int, month: Optional[int] = None
    ) -> list[datetime_date]:
        """Get dates for a specific year, optionally filtered by month."""
        year_folder = self.folder / str(year)
        if not year_folder.exists():
            return []

        dates: list[datetime_date] = []

        if month is not None:
            dates.extend(self._get_dates_for_month(year_folder, year, month))
        else:
            for month_num in range(1, 13):
                dates.extend(self._get_dates_for_month(year_folder, year, month_num))

        return sorted(dates)

    def _get_dates_for_all_years(self) -> list[datetime_date]:
        """Get dates for all available years."""
        dates: list[datetime_date] = []

        for year_folder in self.folder.iterdir():
            if year_folder.is_dir() and year_folder.name.isdigit():
                year_num = int(year_folder.name)
                dates.extend(self._get_dates_for_year(year_num))

        return sorted(dates)

    def _get_dates_for_month(
        self, year_folder: pathlib.Path, year: int, month: int
    ) -> list[datetime_date]:
        """Get dates for a specific month within a year folder."""
        month_folder = year_folder / MONTHS_SHORT[month - 1]
        if month_folder.exists():
            return self._get_dates_from_month_folder(month_folder, year, month)
        return []

    def _get_dates_from_month_folder(
        self, month_folder: pathlib.Path, year: int, month: int
    ) -> list[datetime_date]:
        dates = []
        for file_path in month_folder.glob("*.csv"):
            try:
                day = int(file_path.stem)
                if 1 <= day <= 31:  # Basic validation
                    dates.append(datetime_date(year, month, day))
            except (ValueError, OSError):
                continue  # Skip invalid files
        return dates

    def cleanup_empty_directories(self) -> None:
        """Remove empty year and month directories.

        This helps keep the filesystem structure clean.
        """
        try:
            for year_folder in self.folder.iterdir():
                if year_folder.is_dir():
                    for month_folder in year_folder.iterdir():
                        if month_folder.is_dir() and not any(month_folder.iterdir()):
                            month_folder.rmdir()
                            self._logger.debug(
                                f"Removed empty month folder: {month_folder}"
                            )

                    if not any(year_folder.iterdir()):
                        year_folder.rmdir()
                        self._logger.debug(f"Removed empty year folder: {year_folder}")

        except Exception as e:
            self._logger.warning(f"Failed to cleanup empty directories: {e}")

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[object],
    ) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            traceback: Exception traceback
        """
        self.cleanup_empty_directories()
