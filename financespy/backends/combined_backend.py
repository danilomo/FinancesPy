"""Combined backend that merges transactions from multiple accounts."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date as datetime_date
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from financespy.backend import Backend
from financespy.categories import Categories, Category
from financespy.exceptions import BackendError, DataValidationError
from financespy.models import TransactionModel
from financespy.predicate_compiler import compile_predicate
from financespy.transaction import Transaction

if TYPE_CHECKING:
    from financespy.account import Account


class CombinedBackend(Backend):
    """Backend that combines transactions from multiple sub-accounts.

    This backend provides a unified read-only view of multiple accounts.
    Each transaction from sub-accounts is tagged with the account name
    as an additional category.

    Features:
    - Read-only (insert_record raises exception)
    - Supports exclude predicates per sub-account
    - Validates currency consistency
    - Handles sub-account query failures gracefully

    Args:
        folder: Path to the combined account folder
        categories: Category system for transaction categorization
        config: Full account.json configuration dict

    Raises:
        DataValidationError: If configuration is invalid
        BackendError: If sub-account initialization fails
    """

    def __init__(
        self, folder: Path, categories: Categories, config: dict[str, Any]
    ) -> None:
        """Initialize combined backend."""
        super().__init__(categories)

        self._config = config
        self._folder = Path(folder)
        self._sub_accounts: list[dict[str, Any]] = []

        self._logger.info("Initializing CombinedBackend")

        # Validate configuration and initialize sub-accounts
        self._validate_config()
        self._initialize_sub_accounts()

        self._logger.info(
            f"CombinedBackend initialized with {len(self._sub_accounts)} sub-accounts"
        )

    def _validate_config(self) -> None:
        """Validate the combined account configuration.

        Raises:
            DataValidationError: If configuration is invalid
        """
        if not isinstance(self._config, dict):
            raise DataValidationError("Configuration must be a dictionary")

        if "accounts" not in self._config:
            raise DataValidationError("Configuration must contain 'accounts' list")

        accounts = self._config["accounts"]
        if not isinstance(accounts, list):
            raise DataValidationError("'accounts' must be a list")

        if len(accounts) == 0:
            raise DataValidationError("At least one sub-account must be specified")

        # Validate each account configuration
        for idx, account_config in enumerate(accounts):
            if not isinstance(account_config, dict):
                raise DataValidationError(
                    f"Account at index {idx} must be a dictionary"
                )

            if "name" not in account_config:
                raise DataValidationError(
                    f"Account at index {idx} is missing required 'name' field"
                )

            if "path" not in account_config:
                raise DataValidationError(
                    f"Account at index {idx} is missing required 'path' field"
                )

            # Validate exclude predicates if present
            if "exclude" in account_config:
                exclude = account_config["exclude"]
                if not isinstance(exclude, list):
                    raise DataValidationError(
                        f"Account '{account_config['name']}': "
                        f"'exclude' must be a list of strings"
                    )

                for predicate_expr in exclude:
                    if not isinstance(predicate_expr, str):
                        raise DataValidationError(
                            f"Account '{account_config['name']}': "
                            f"exclude predicates must be strings"
                        )

    def _initialize_sub_accounts(self) -> None:
        """Initialize all sub-accounts.

        Opens each sub-account, validates currency consistency,
        and compiles exclude predicates.

        Raises:
            BackendError: If sub-account initialization fails
            DataValidationError: If currency validation fails
        """
        # Import here to avoid circular imports
        from financespy.account import open_account

        for account_config in self._config.get("accounts", []):
            account_name = account_config["name"]
            account_path = account_config["path"]

            self._logger.debug(f"Initializing sub-account '{account_name}'")

            try:
                # Resolve relative paths relative to combined account folder
                if not os.path.isabs(account_path):
                    account_path = str(self._folder / account_path)

                # Open sub-account using factory (handles any backend type)
                sub_account = open_account(account_path)

                if sub_account is None:
                    raise BackendError(
                        f"Failed to open sub-account '{account_name}' at path: {account_path}"
                    )

                # Validate currency consistency
                self._validate_currency(sub_account, account_name)

                # Compile exclude predicates
                exclude_predicates: list[Callable[[Transaction], bool]] = []
                for expr in account_config.get("exclude", []):
                    try:
                        predicate = compile_predicate(expr)
                        exclude_predicates.append(predicate)
                        self._logger.debug(
                            f"Compiled exclude predicate for '{account_name}': {expr}"
                        )
                    except Exception as e:
                        raise BackendError(
                            f"Invalid exclude predicate in account '{account_name}': "
                            f"{expr} - {e}"
                        ) from e

                # Store sub-account info
                self._sub_accounts.append(
                    {
                        "name": account_name,
                        "backend": sub_account.backend,
                        "exclude_predicates": exclude_predicates,
                        "account_obj": sub_account,
                    }
                )

                self._logger.info(
                    f"Sub-account '{account_name}' initialized successfully"
                )

            except BackendError:
                raise
            except DataValidationError:
                raise
            except Exception as e:
                raise BackendError(
                    f"Failed to initialize sub-account '{account_name}': {e}"
                ) from e

    def _validate_currency(self, sub_account: Account, account_name: str) -> None:
        """Validate that sub-account currency matches combined account.

        Args:
            sub_account: The sub-account to validate
            account_name: Name of the sub-account (for error messages)

        Raises:
            DataValidationError: If currency mismatch detected
        """
        expected_currency = self._config.get("currency", "").lower()
        actual_currency = sub_account.metadata.currency.lower()

        if expected_currency and actual_currency != expected_currency:
            raise DataValidationError(
                f"Currency mismatch in account '{account_name}': "
                f"expected '{expected_currency}', got '{actual_currency}'"
            )

    def _clone_and_tag_transaction(
        self, transaction: Transaction, account_name: str
    ) -> Transaction:
        """Clone transaction and add account name as extra category.

        Args:
            transaction: Original transaction to clone
            account_name: Name of source account

        Returns:
            Cloned transaction with account category added
        """
        # Create new transaction with same attributes
        cloned = Transaction(
            value=transaction.value,
            description=transaction.description,
            categories=transaction.categories.copy(),  # Shallow copy
            id=transaction.id,
            date=transaction.date,
        )

        # Add account name as a category
        # Check if account name exists in categories, otherwise create it
        account_category = self.categories.category(account_name)

        # If category() returned the default category and it's not the account name,
        # create a new category for the account name
        if str(account_category) != account_name:
            account_category = Category(account_name, parent=None)

        cloned.add_category(account_category)

        return cloned

    def records(self, date: datetime_date) -> Iterator[Transaction]:
        """Get all records for a specific date from all sub-accounts.

        Queries all sub-accounts, applies exclude filters, and merges
        transactions with account name tags.

        Args:
            date: Date to query

        Returns:
            Iterator of merged transactions

        Raises:
            DataValidationError: If date is invalid
            BackendError: If all sub-accounts fail to query
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        try:
            all_transactions: list[Transaction] = []
            errors: list[str] = []

            # Query each sub-account
            for account_info in self._sub_accounts:
                account_name = account_info["name"]
                backend = account_info["backend"]
                exclude_predicates = account_info["exclude_predicates"]

                try:
                    # Get transactions from sub-account
                    for transaction in backend.records(date):
                        # Apply exclude filters
                        excluded = False
                        for predicate in exclude_predicates:
                            try:
                                if predicate(transaction):
                                    excluded = True
                                    self._logger.debug(
                                        f"Transaction excluded in '{account_name}': "
                                        f"{transaction.description}"
                                    )
                                    break
                            except Exception as e:
                                self._logger.warning(
                                    f"Filter evaluation error for '{account_name}': {e}"
                                )
                                # Continue processing on filter errors
                                continue

                        if excluded:
                            continue

                        # Clone transaction and add account name as category
                        cloned_transaction = self._clone_and_tag_transaction(
                            transaction, account_name
                        )
                        all_transactions.append(cloned_transaction)

                except Exception as e:
                    error_msg = (
                        f"Error querying account '{account_name}' for {date}: {e}"
                    )
                    self._logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with other accounts

            # If all accounts failed, raise error
            if len(errors) == len(self._sub_accounts) and len(errors) > 0:
                raise BackendError(
                    f"All sub-accounts failed to query. Errors: {'; '.join(errors)}"
                )

            return iter(all_transactions)

        except DataValidationError:
            raise
        except BackendError:
            raise
        except Exception as e:
            self._logger.error(f"Failed to retrieve records for date {date}: {e}")
            raise BackendError(f"Query operation failed: {e}") from e

    def insert_record(
        self,
        date: datetime_date,
        transaction: Transaction | TransactionModel | str,
    ) -> str:
        """Raise exception - CombinedBackend is read-only.

        Args:
            date: Transaction date (ignored)
            transaction: Transaction to insert (ignored)

        Raises:
            BackendError: Always raises - backend is read-only
        """
        raise BackendError(
            "CombinedBackend is read-only. Cannot insert records. "
            "Insert records into individual sub-accounts instead."
        )

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit - cleanup sub-account backends.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            traceback: Exception traceback
        """
        self._logger.debug("Cleaning up CombinedBackend")

        for account_info in self._sub_accounts:
            try:
                account_obj = account_info.get("account_obj")
                if account_obj and hasattr(account_obj.backend, "__exit__"):
                    account_obj.backend.__exit__(exc_type, exc_value, traceback)
            except Exception as e:
                self._logger.warning(
                    f"Error closing sub-account '{account_info['name']}': {e}"
                )

        # Clear references
        self._sub_accounts.clear()
        self._logger.info("CombinedBackend cleanup complete")
