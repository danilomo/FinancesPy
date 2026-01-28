"""Read-only backend for loading transactions from CSV files in a folder."""

from __future__ import annotations

import csv
import json
import logging
import pathlib
import re
from collections.abc import Iterator
from datetime import date
from typing import Any

from financespy.backend import Backend
from financespy.backends.memory_backend import MemoryBackend
from financespy.categories import Categories, categories_from_list
from financespy.exceptions import BackendConnectionError, BackendError
from financespy.money import Money
from financespy.transaction import Transaction


class CsvFolderBackend(Backend):
    """Read-only backend for loading transactions from CSV files in a folder.

    This backend recursively loads all CSV files from a folder into an internal
    MemoryBackend on initialization. It is read-only - insert operations will
    raise BackendError.

    Folder structure:
        data/
            categories.json    # Category definitions
            02-02-2025_groceries.csv
            02-02-2025_utilities.csv
            subdir/
                03-02-2025_travel.csv

    Filename format: DD-MM-YYYY(_category)?((number))?.csv
        - 02-02-2025.csv - just date
        - 02-02-2025_groceries.csv - date + category
        - 02-02-2025_groceries(1).csv - date + category + sequence number
        - 02-02-2025_d_m(2).csv - categories with underscores work correctly

    CSV format: description, value, categories (semicolon-separated)
        - "Monthly subscription", 9.99, utilities
        - "Bread", 2.50, "groceries;bakery"
    """

    # Pattern captures: day, month, year, optional category, optional visit number
    # Format: DD-MM-YYYY(_category)?(\(N\))?.csv
    # Examples: 02-02-2025.csv, 02-02-2025_edeka.csv, 02-02-2025_edeka(1).csv
    FILENAME_PATTERN = re.compile(
        r"^(\d{2})-(\d{2})-(\d{4})(?:_([^()]+))?(?:\((\d+)\))?\.csv$"
    )

    def __init__(
        self, folder: str | pathlib.Path, categories: Categories | None = None
    ) -> None:
        """Initialize the CSV folder backend.

        Args:
            folder: Path to the folder containing CSV files
            categories: Optional categories object. If not provided, will be
                       loaded from categories.json in the folder root.

        Raises:
            BackendConnectionError: If folder doesn't exist or is empty
            BackendError: If categories.json is missing or invalid
        """
        self._folder = pathlib.Path(folder)
        self._logger = logging.getLogger(self.__class__.__name__)

        # Validate folder exists
        if not self._folder.exists():
            raise BackendConnectionError(f"Folder does not exist: {self._folder}")

        if not self._folder.is_dir():
            raise BackendConnectionError(f"Path is not a directory: {self._folder}")

        # Load categories
        if categories is None:
            categories = self._load_categories()

        # Initialize parent class
        super().__init__(categories)

        # Create internal memory backend
        self._memory_backend = MemoryBackend(categories)

        # Load all CSV files
        self._load_all_csv_files()

        self._logger.info(
            f"CsvFolderBackend initialized with {self._memory_backend.get_record_count()} records"
        )

    def _load_categories(self) -> Categories:
        """Load categories from categories.json at folder root.

        Returns:
            Categories object

        Raises:
            BackendError: If categories.json is missing or invalid
        """
        categories_file = self._folder / "categories.json"

        if not categories_file.exists():
            raise BackendError(f"categories.json not found in folder: {self._folder}")

        try:
            with open(categories_file, encoding="utf-8") as f:
                categories_data = json.load(f)

            if not isinstance(categories_data, list):
                raise BackendError(
                    f"categories.json must contain a JSON array: {categories_file}"
                )

            return categories_from_list(categories_data)

        except json.JSONDecodeError as e:
            raise BackendError(
                f"Invalid JSON in categories.json: {categories_file}: {e}"
            ) from e
        except Exception as e:
            if isinstance(e, BackendError):
                raise
            raise BackendError(
                f"Error loading categories from {categories_file}: {e}"
            ) from e

    def _parse_filename(self, filename: str) -> tuple[date, str | None] | None:
        """Extract date and optional category from filename.

        Args:
            filename: Filename to parse (e.g., "02-02-2025_edeka.csv")

        Returns:
            Tuple of (date, category) or None if filename doesn't match pattern.
            Category may be None if not present in filename.
        """
        match = self.FILENAME_PATTERN.match(filename)
        if not match:
            return None

        day_str, month_str, year_str, category, _visit_number = match.groups()

        try:
            file_date = date(year=int(year_str), month=int(month_str), day=int(day_str))
            return (file_date, category)
        except ValueError:
            # Invalid date (e.g., 31-02-2025)
            return None

    def _load_all_csv_files(self) -> None:
        """Recursively find and load all CSV files in the folder."""
        csv_files = list(self._folder.rglob("*.csv"))

        if not csv_files:
            self._logger.warning(f"No CSV files found in folder: {self._folder}")
            return

        loaded_count = 0
        skipped_count = 0

        for csv_path in csv_files:
            parsed = self._parse_filename(csv_path.name)

            if parsed is None:
                self._logger.warning(
                    f"Skipping file with invalid filename format: {csv_path.name}"
                )
                skipped_count += 1
                continue

            file_date, filename_category = parsed

            try:
                records_loaded = self._load_csv_file(
                    csv_path, file_date, filename_category
                )
                loaded_count += records_loaded
            except Exception as e:
                self._logger.warning(f"Error loading CSV file {csv_path}: {e}")
                skipped_count += 1

        self._logger.info(
            f"Loaded {loaded_count} records from CSV files, "
            f"skipped {skipped_count} files"
        )

    def _load_csv_file(
        self, path: pathlib.Path, file_date: date, filename_category: str | None
    ) -> int:
        """Load a single CSV file.

        Args:
            path: Path to the CSV file
            file_date: Date extracted from filename
            filename_category: Optional category from filename

        Returns:
            Number of records loaded from this file
        """
        records_loaded = 0

        try:
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.reader(f)

                for row_num, row in enumerate(reader, start=1):
                    if not row or all(cell.strip() == "" for cell in row):
                        # Skip empty rows
                        continue

                    try:
                        transaction = self._parse_csv_row(
                            row, file_date, filename_category, path.name, row_num
                        )
                        self._memory_backend.insert_record(file_date, transaction)
                        records_loaded += 1
                    except Exception as e:
                        self._logger.warning(
                            f"Error parsing row {row_num} in {path.name}: {e}"
                        )

        except Exception as e:
            self._logger.warning(f"Error reading CSV file {path}: {e}")
            raise

        return records_loaded

    def _parse_csv_row(
        self,
        row: list[str],
        file_date: date,
        filename_category: str | None,
        filename: str,
        row_num: int,
    ) -> Transaction:
        """Parse a CSV row into a Transaction.

        CSV format: description, value, categories (semicolon-separated)

        Args:
            row: List of CSV cell values
            file_date: Date for the transaction
            filename_category: Optional category from filename to add
            filename: Filename for error messages
            row_num: Row number for error messages

        Returns:
            Transaction object

        Raises:
            ValueError: If row format is invalid
        """
        if len(row) < 2:
            raise ValueError(
                f"Row must have at least 2 columns (description, value), "
                f"got {len(row)}"
            )

        description = row[0].strip()
        value_str = row[1].strip()

        # Parse value
        try:
            value = Money(value_str)
        except Exception as e:
            raise ValueError(f"Invalid value '{value_str}': {e}") from e

        # Parse categories
        category_names: list[str] = []

        if len(row) >= 3 and row[2].strip():
            # Categories are semicolon-separated in column 3
            raw_categories = row[2].strip()
            category_names = [c.strip() for c in raw_categories.split(";") if c.strip()]

        # If no categories, use description as category (matches parse_transaction behavior)
        if not category_names:
            category_names = [description]

        # Add filename category if present
        if filename_category:
            category_names.append(filename_category)

        # Resolve category names to Category objects
        categories_list = [self.categories.category(name) for name in category_names]

        return Transaction(
            value=value,
            description=description,
            categories=categories_list,
            date=file_date,
        )

    def records(self, date: date) -> Iterator[Transaction]:
        """Get all records for a specific date.

        Args:
            date: Date to query

        Returns:
            Iterator of transactions for the date
        """
        return self._memory_backend.records(date)

    def insert_record(self, date: date, transaction: Any) -> str:
        """Insert operation is not supported - this backend is read-only.

        Raises:
            BackendError: Always raised as this backend is read-only
        """
        raise BackendError("CsvFolderBackend is read-only")

    def get_record_count(self) -> int:
        """Get total count of records loaded.

        Returns:
            Total number of records stored
        """
        return self._memory_backend.get_record_count()

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit."""
        pass
