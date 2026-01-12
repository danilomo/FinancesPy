"""Tests for account.py module - external categories file support."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from financespy.account import OpenAccountError, read_metadata


class TestExternalCategories:
    """Test suite for external categories file loading."""

    def test_inline_categories_still_work(self):
        """Regression test: inline categories array should still work."""
        categories_data = [
            "uncategorized",
            "random",
            {"food": ["groceries", "restaurant"]},
            {"transport": ["bus", "train"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": categories_data,
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            metadata = read_metadata(account_json)

            assert metadata.name == "test_account"
            assert metadata.backend_type == "xlsx"
            assert metadata.currency == "eur"
            assert metadata.categories is not None
            # Verify some categories exist
            assert "uncategorized" in metadata.categories._categories
            assert "groceries" in metadata.categories._categories
            assert "restaurant" in metadata.categories._categories

    def test_relative_path_loading(self):
        """Test loading categories from relative path."""
        categories_data = [
            "uncategorized",
            "random",
            {"food": ["groceries", "restaurant"]},
            {"transport": ["bus", "train"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create categories.json
            categories_json = Path(tmpdir) / "categories.json"
            with open(categories_json, "w") as f:
                json.dump(categories_data, f)

            # Create account folder with account.json
            account_folder = Path(tmpdir) / "account"
            account_folder.mkdir()
            account_json = account_folder / "account.json"

            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "../categories.json",  # Relative path
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            metadata = read_metadata(account_json)

            assert metadata.name == "test_account"
            assert metadata.backend_type == "xlsx"
            assert metadata.currency == "eur"
            assert metadata.categories is not None
            # Verify categories were loaded from external file
            assert "uncategorized" in metadata.categories._categories
            assert "groceries" in metadata.categories._categories
            assert "restaurant" in metadata.categories._categories

    def test_absolute_path_loading(self):
        """Test loading categories from absolute path."""
        categories_data = [
            "uncategorized",
            "random",
            {"food": ["groceries", "restaurant"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create categories.json with absolute path
            categories_json = Path(tmpdir) / "categories.json"
            with open(categories_json, "w") as f:
                json.dump(categories_data, f)

            # Create account.json in different location
            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": str(categories_json),  # Absolute path
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            metadata = read_metadata(account_json)

            assert metadata.categories is not None
            assert "uncategorized" in metadata.categories._categories
            assert "groceries" in metadata.categories._categories

    def test_file_not_found_error(self):
        """Test error handling when categories file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "nonexistent.json",  # File doesn't exist
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            with pytest.raises(OpenAccountError) as exc_info:
                read_metadata(account_json)

            assert "Categories file not found" in str(exc_info.value)

    def test_invalid_json_error(self):
        """Test error handling for malformed JSON in categories file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON file
            categories_json = Path(tmpdir) / "categories.json"
            with open(categories_json, "w") as f:
                f.write("{invalid json content")

            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "categories.json",
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            with pytest.raises(OpenAccountError) as exc_info:
                read_metadata(account_json)

            assert "Invalid JSON in categories file" in str(exc_info.value)

    def test_invalid_data_type_error(self):
        """Test error when categories file contains object instead of array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create categories.json with object instead of array
            categories_json = Path(tmpdir) / "categories.json"
            invalid_data = {"categories": ["food", "transport"]}  # Wrapped in object

            with open(categories_json, "w") as f:
                json.dump(invalid_data, f)

            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "categories.json",
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            with pytest.raises(OpenAccountError) as exc_info:
                read_metadata(account_json)

            assert "must contain a JSON array" in str(exc_info.value)

    def test_empty_categories_file(self):
        """Test that empty categories file works (edge case)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty categories array
            categories_json = Path(tmpdir) / "categories.json"
            with open(categories_json, "w") as f:
                json.dump([], f)

            account_json = Path(tmpdir) / "account.json"
            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "categories.json",
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            metadata = read_metadata(account_json)

            # Should work, categories_from_list handles empty list
            assert metadata.categories is not None

    def test_nested_relative_paths(self):
        """Test loading categories from nested relative paths."""
        categories_data = [
            "uncategorized",
            {"food": ["groceries"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            shared_folder = Path(tmpdir) / "shared"
            shared_folder.mkdir()
            categories_json = shared_folder / "categories.json"

            with open(categories_json, "w") as f:
                json.dump(categories_data, f)

            # Create account in different nested folder
            accounts_folder = Path(tmpdir) / "accounts" / "checking"
            accounts_folder.mkdir(parents=True)
            account_json = accounts_folder / "account.json"

            account_data = {
                "name": "test_account",
                "type": "xlsx",
                "currency": "eur",
                "categories": "../../shared/categories.json",  # Nested relative path
                "properties": {},
            }

            with open(account_json, "w") as f:
                json.dump(account_data, f)

            metadata = read_metadata(account_json)

            assert metadata.categories is not None
            assert "uncategorized" in metadata.categories._categories
            assert "groceries" in metadata.categories._categories
