"""Tests for CsvFolderBackend."""

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from financespy.account import open_account
from financespy.backends.csv_folder_backend import CsvFolderBackend
from financespy.categories import categories_from_list
from financespy.exceptions import BackendConnectionError, BackendError


@pytest.fixture
def csv_folder():
    """Path to the test CSV folder."""
    return Path(__file__).parent / "resources" / "receipts"


@pytest.fixture
def test_categories():
    """Categories for testing."""
    return categories_from_list(
        [
            {
                "expenses": [
                    {"others": ["uncategorized"]},
                    {
                        "food": [
                            {"groceries": ["lidl", "aldi", "edeka", "rewe"]},
                            "bakery",
                        ]
                    },
                ]
            }
        ]
    )


class TestFilenamePattern:
    """Tests for filename pattern parsing."""

    def test_parse_date_only(self, csv_folder, test_categories):
        """Test parsing filename with date only."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        result = backend._parse_filename("02-02-2025.csv")

        assert result is not None
        assert result[0] == date(2025, 2, 2)
        assert result[1] is None

    def test_parse_date_with_category(self, csv_folder, test_categories):
        """Test parsing filename with date and category."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        result = backend._parse_filename("02-02-2025_edeka.csv")

        assert result is not None
        assert result[0] == date(2025, 2, 2)
        assert result[1] == "edeka"

    def test_parse_date_with_category_and_number(self, csv_folder, test_categories):
        """Test parsing filename with date, category, and visit number."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        result = backend._parse_filename("02-02-2025_edeka(1).csv")

        assert result is not None
        assert result[0] == date(2025, 2, 2)
        assert result[1] == "edeka"

    def test_parse_date_with_underscore_category(self, csv_folder, test_categories):
        """Test parsing filename with underscore in category name."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        result = backend._parse_filename("02-02-2025_asia_market.csv")

        assert result is not None
        assert result[0] == date(2025, 2, 2)
        assert result[1] == "asia_market"

    def test_parse_date_with_underscore_category_and_number(
        self, csv_folder, test_categories
    ):
        """Test parsing filename with underscore in category and visit number."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        result = backend._parse_filename("02-02-2025_d_m(2).csv")

        assert result is not None
        assert result[0] == date(2025, 2, 2)
        assert result[1] == "d_m"

    def test_parse_invalid_filename(self, csv_folder, test_categories):
        """Test parsing invalid filename returns None."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        assert backend._parse_filename("invalid.csv") is None
        assert backend._parse_filename("2025-02-02.csv") is None  # Wrong date format
        assert backend._parse_filename("02-02-25.csv") is None  # 2-digit year
        assert backend._parse_filename("receipt.txt") is None  # Wrong extension

    def test_parse_invalid_date(self, csv_folder, test_categories):
        """Test parsing filename with invalid date returns None."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        # Invalid day (31st February)
        assert backend._parse_filename("31-02-2025.csv") is None
        # Invalid month
        assert backend._parse_filename("15-13-2025.csv") is None


class TestCSVParsing:
    """Tests for CSV row parsing."""

    def test_parse_basic_row(self, csv_folder, test_categories):
        """Test parsing a basic CSV row."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        transaction = backend._parse_csv_row(
            ["Milk 1L", "1.29", "groceries"], date(2025, 2, 2), None, "test.csv", 1
        )

        assert transaction.description == "Milk 1L"
        assert transaction.value._cents == 129
        assert transaction.date == date(2025, 2, 2)
        assert transaction.matches_category("groceries")

    def test_parse_row_with_filename_category(self, csv_folder, test_categories):
        """Test that filename category is added to transaction categories."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        transaction = backend._parse_csv_row(
            ["Milk 1L", "1.29", "groceries"], date(2025, 2, 2), "edeka", "test.csv", 1
        )

        assert transaction.matches_category("groceries")
        assert transaction.matches_category("edeka")

    def test_parse_row_with_multiple_categories(self, csv_folder, test_categories):
        """Test parsing row with semicolon-separated categories."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        transaction = backend._parse_csv_row(
            ["Bread", "2.50", "groceries;bakery"], date(2025, 2, 2), None, "test.csv", 1
        )

        assert transaction.matches_category("groceries")
        assert transaction.matches_category("bakery")

    def test_parse_row_without_category_uses_description(
        self, csv_folder, test_categories
    ):
        """Test that description is used as category when no category specified."""
        backend = CsvFolderBackend(csv_folder, test_categories)
        transaction = backend._parse_csv_row(
            ["groceries", "1.29"], date(2025, 2, 2), None, "test.csv", 1
        )

        # Description "groceries" should be used as category
        assert transaction.description == "groceries"
        assert transaction.matches_category("groceries")

    def test_parse_row_invalid_too_few_columns(self, csv_folder, test_categories):
        """Test that rows with too few columns raise ValueError."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        with pytest.raises(ValueError, match="at least 2 columns"):
            backend._parse_csv_row(["Milk"], date(2025, 2, 2), None, "test.csv", 1)

    def test_parse_row_invalid_value(self, csv_folder, test_categories):
        """Test that invalid value raises ValueError."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        with pytest.raises(ValueError, match="Invalid value"):
            backend._parse_csv_row(
                ["Milk", "not_a_number", "groceries"],
                date(2025, 2, 2),
                None,
                "test.csv",
                1,
            )


class TestBackendLoading:
    """Tests for backend initialization and loading."""

    def test_load_csv_folder(self, csv_folder, test_categories):
        """Test loading receipts from folder."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        # Should have loaded all records from test fixtures
        # 02-02-2025_edeka.csv: 3 records
        # 02-02-2025_lidl.csv: 2 records
        # subdir/03-02-2025_rewe.csv: 3 records
        # 05-02-2025.csv: 2 records
        # Total: 10 records
        assert backend.get_record_count() == 10

    def test_load_categories_from_json(self, csv_folder):
        """Test loading categories from categories.json."""
        backend = CsvFolderBackend(csv_folder)

        # Should have loaded categories from categories.json
        assert backend.categories is not None
        assert backend.categories.category("groceries") is not None

    def test_recursive_loading(self, csv_folder, test_categories):
        """Test that CSV files in subdirectories are loaded."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        # Check records from subdir/03-02-2025_rewe.csv
        records = list(backend.records(date(2025, 2, 3)))
        assert len(records) == 3

        # Verify rewe category is added from filename
        for record in records:
            assert record.matches_category("rewe")

    def test_filename_category_added(self, csv_folder, test_categories):
        """Test that filename category is added to all transactions in file."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        # Records from 02-02-2025_edeka.csv should have edeka category
        records = list(backend.records(date(2025, 2, 2)))
        edeka_records = [r for r in records if r.matches_category("edeka")]
        assert len(edeka_records) == 3

        # Records from 02-02-2025_lidl.csv should have lidl category
        lidl_records = [r for r in records if r.matches_category("lidl")]
        assert len(lidl_records) == 2


class TestReadOnlyEnforcement:
    """Tests for read-only behavior."""

    def test_insert_raises_error(self, csv_folder, test_categories):
        """Test that insert_record raises BackendError."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        with pytest.raises(BackendError, match="read-only"):
            backend.insert_record(date(2025, 2, 2), "10, groceries")


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_folder_raises_error(self, test_categories):
        """Test that missing folder raises BackendConnectionError."""
        with pytest.raises(BackendConnectionError, match="does not exist"):
            CsvFolderBackend("/nonexistent/folder", test_categories)

    def test_file_not_directory_raises_error(self, csv_folder, test_categories):
        """Test that passing a file path raises BackendConnectionError."""
        file_path = csv_folder / "categories.json"

        with pytest.raises(BackendConnectionError, match="not a directory"):
            CsvFolderBackend(file_path, test_categories)

    def test_missing_categories_json_raises_error(self):
        """Test that missing categories.json raises BackendError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(BackendError, match="categories.json not found"):
                CsvFolderBackend(tmpdir)

    def test_invalid_categories_json_raises_error(self):
        """Test that invalid JSON in categories.json raises BackendError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            categories_file = Path(tmpdir) / "categories.json"
            categories_file.write_text("not valid json")

            with pytest.raises(BackendError, match="Invalid JSON"):
                CsvFolderBackend(tmpdir)

    def test_categories_json_not_array_raises_error(self):
        """Test that non-array categories.json raises BackendError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            categories_file = Path(tmpdir) / "categories.json"
            categories_file.write_text('{"not": "an array"}')

            with pytest.raises(BackendError, match="must contain a JSON array"):
                CsvFolderBackend(tmpdir)

    def test_invalid_filename_skipped_with_warning(self, test_categories, caplog):
        """Test that files with invalid filenames are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create categories.json
            categories_file = Path(tmpdir) / "categories.json"
            categories_file.write_text(
                json.dumps([{"expenses": [{"others": ["uncategorized"]}]}])
            )

            # Create file with invalid filename
            invalid_file = Path(tmpdir) / "invalid_name.csv"
            invalid_file.write_text("Milk,1.29,groceries\n")

            # Create valid file
            valid_file = Path(tmpdir) / "02-02-2025.csv"
            valid_file.write_text("Bread,2.50,groceries\n")

            backend = CsvFolderBackend(tmpdir, test_categories)

            # Should have loaded only the valid file
            assert backend.get_record_count() == 1


class TestTimeIterators:
    """Tests for time-based iterators."""

    def test_day_iterator(self, csv_folder, test_categories):
        """Test day iterator returns correct records."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        day = backend.day(2, 2, 2025)
        records = list(day.records())

        # Should have 5 records from 02-02-2025 (edeka + lidl)
        assert len(records) == 5

    def test_month_iterator(self, csv_folder, test_categories):
        """Test month iterator returns correct records."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        month = backend.month(2, 2025)
        records = list(month.records())

        # All test records are in February 2025
        assert len(records) == 10


class TestAccountIntegration:
    """Tests for integration with open_account."""

    def test_open_account_csv_folder(self, csv_folder):
        """Test opening CSV folder via open_account."""
        account = open_account(str(csv_folder))

        assert account is not None
        assert account.metadata.backend_type == "csv_folder"
        assert account.metadata.name == "csv_folder_test"

        # Should have loaded all records
        records = list(account.month(2, 2025).records())
        assert len(records) == 10


class TestQuotedCSV:
    """Tests for handling quoted CSV fields."""

    def test_quoted_description_with_comma(self, csv_folder, test_categories):
        """Test that quoted descriptions with commas are handled correctly."""
        backend = CsvFolderBackend(csv_folder, test_categories)

        # The 05-02-2025.csv file contains: "Coffee, ground",5.99,groceries
        records = list(backend.records(date(2025, 2, 5)))

        coffee_record = next(r for r in records if "Coffee" in r.description)
        assert coffee_record.description == "Coffee, ground"
        assert coffee_record.value._cents == 599
