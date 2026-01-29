"""SQL database backend implementation for FinancesPy."""

import json
from collections.abc import Iterator
from datetime import date as datetime_date
from datetime import datetime
from typing import Any, Optional, cast

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Integer,
    String,
    Text,
    and_,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.types import JSON, TypeDecorator

import financespy.transaction
from financespy.account import AccountMetadata
from financespy.backend import Backend
from financespy.backends.memory_backend import month_iterator_from_query
from financespy.categories import Categories, categories_from_list
from financespy.exceptions import (
    BackendConnectionError,
    BackendError,
    DataValidationError,
)
from financespy.money import Money
from financespy.sql_predicate_compiler import SQLPredicateCompiler, SQLDialect
from financespy.time_factory import parse_month


class BaseType(DeclarativeMeta):
    pass


Base: type[Any] = declarative_base(metaclass=BaseType)


class JSONType(TypeDecorator):
    """Cross-database JSON type that uses JSONB on PostgreSQL, JSON elsewhere."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        elif dialect.name in ("mysql", "mariadb", "sqlite"):
            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name not in ("postgresql", "mysql", "mariadb", "sqlite"):
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, str):
                return json.loads(value)
        return value


class Account(Base):
    """Account model for storing account metadata."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    categories = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    currency = Column(String(10), nullable=False)
    user_id = Column(Integer, nullable=True)
    created_at = Column(Date, nullable=False)


class Transaction(Base):
    """Transaction model for storing transaction data."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(BigInteger, nullable=False)  # Stored in cents
    description = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)  # Original categories (comma-separated)
    category_membership = Column(JSONType, nullable=True)  # {"cat": true} for querying
    account_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)


def read_account_metadata(
    session: "Session", account_id: int
) -> Optional[AccountMetadata]:
    """Read account metadata from database.

    Args:
        session: SQLAlchemy session
        account_id: Account ID to read
        account_model: Account model class

    Returns:
        AccountMetadata object or None if not found

    Raises:
        BackendError: If database operation fails
    """
    try:
        query = session.query(Account).filter(Account.id == account_id)
        results = query.all()

        if not results:
            return None

        row = results[0]

        try:
            categories_data = json.loads(cast(str, row.categories))
            categories = categories_from_list(categories_data)
        except json.JSONDecodeError as e:
            raise BackendError(
                f"Invalid categories data for account {account_id}: {e}"
            ) from e

        if categories is None:
            raise BackendError(f"No valid categories found for account {account_id}")

        return AccountMetadata(
            categories=categories,
            currency=cast(str, row.currency),
            name=cast(str, row.name),
            properties={},
            backend_type="sql",
        )

    except SQLAlchemyError as e:
        raise BackendError(f"Database error reading account {account_id}: {e}") from e


class SQLBackend(Backend):
    """SQL database backend for transaction storage.

    Provides transaction storage using SQLAlchemy with support for
    multiple database engines (PostgreSQL, MySQL, SQLite, etc.).
    """

    def __init__(
        self,
        account_id: int,
        session: "Session",
        categories: Categories,
    ) -> None:
        """Initialize SQL backend.

        Args:
            account_id: Account ID for this backend instance
            session: SQLAlchemy session
            transaction_model: Transaction SQLAlchemy model
            categories: Category system for transaction categorization

        Raises:
            DataValidationError: If parameters are invalid
            BackendConnectionError: If database connection fails
        """
        if not isinstance(account_id, int) or account_id <= 0:
            raise DataValidationError("Account ID must be a positive integer")

        if not session:
            raise DataValidationError("Database session is required")

        # Transaction model is defined as a class, no need to validate

        super().__init__(categories)

        self.session = session
        self.account_id = account_id
        self.categories = categories

        # Test database connection
        try:
            self.session.execute(text("SELECT 1"))
        except Exception as e:
            raise BackendConnectionError(f"Database connection failed: {e}") from e

        self._logger.info(f"SQLBackend initialized for account {account_id}")

    def insert_record(
        self, date: datetime_date, transaction: "financespy.transaction.Transaction"
    ) -> Optional[str]:
        """Insert a transaction record into the database.

        Args:
            date: Transaction date
            transaction: Transaction to insert

        Returns:
            String representation of the generated transaction ID

        Raises:
            DataValidationError: If input validation fails
            BackendError: If database operation fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        if not isinstance(transaction, financespy.transaction.Transaction):
            raise DataValidationError(
                f"Transaction must be a Transaction object, got {type(transaction)}"
            )

        try:
            # Prepare categories string (original format for backward compat)
            categories_str = ""
            category_membership: dict[str, bool] = {}

            if transaction.categories:
                categories_str = ",".join(str(cat) for cat in transaction.categories)
                # Build category membership map with all ancestors
                for cat in transaction.categories:
                    for ancestor_name in cat.ancestor_names(include_self=True):
                        category_membership[ancestor_name] = True

            # Create instance using the model class constructor
            db_transaction = Transaction(
                value=(
                    transaction.value.cents()
                    if hasattr(transaction.value, "cents")
                    else int(transaction.value)
                ),
                description=transaction.description or "",
                categories=categories_str,
                category_membership=category_membership if category_membership else None,
                account_id=self.account_id,
                date=date,
            )

            self.session.add(db_transaction)
            self.session.commit()

            transaction_id = str(db_transaction.id)

            self._logger.debug(f"Inserted transaction {transaction_id} for date {date}")
            return transaction_id

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Failed to insert transaction for date {date}: {e}")
            raise BackendError(f"Database insert failed: {e}") from e
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Unexpected error inserting transaction: {e}")
            raise BackendError(f"Insert operation failed: {e}") from e

    def records(
        self, date: datetime_date
    ) -> Iterator["financespy.transaction.Transaction"]:
        """Get all records for a specific date.

        Args:
            date: Date to query

        Returns:
            Iterator of transactions for the date

        Raises:
            DataValidationError: If date is invalid
            BackendError: If database operation fails
        """
        if not isinstance(date, datetime_date):
            raise DataValidationError(f"Date must be a date object, got {type(date)}")

        try:
            query = self._base_query().filter(Transaction.date == date)

            for db_transaction in query:
                yield self._convert_db_transaction(db_transaction)

        except SQLAlchemyError as e:
            self._logger.error(f"Failed to retrieve records for date {date}: {e}")
            raise BackendError(f"Database query failed: {e}") from e
        except Exception as e:
            self._logger.error(f"Unexpected error retrieving records: {e}")
            raise BackendError(f"Query operation failed: {e}") from e

    def day(
        self, day: int, month: int, year: int
    ) -> Iterator["financespy.transaction.Transaction"]:
        """Get records for a specific day.

        Args:
            day: Day of month (1-31)
            month: Month number (1-12)
            year: Year

        Returns:
            Iterator of transactions for the day

        Raises:
            DataValidationError: If date parameters are invalid
            BackendError: If database operation fails
        """
        self._validate_date_params(day, month, year)

        try:
            target_date = datetime_date(year, month, day)
            return self.records(target_date)
        except ValueError as e:
            raise DataValidationError(f"Invalid date {year}-{month}-{day}: {e}") from e

    def month(self, month: int, year: int) -> Any:
        """Get month iterator for the specified month.

        Args:
            month: Month number (1-12) or month name string (e.g., 'sep', 'september')
            year: Year

        Returns:
            Month iterator object

        Raises:
            DataValidationError: If parameters are invalid
            BackendError: If query fails
        """
        month_num = parse_month(month)
        self._validate_month_year(month_num, year)

        def query(
            first_day: datetime, last_day: datetime
        ) -> Iterator["financespy.transaction.Transaction"]:
            """Query function for month iterator."""
            try:
                db_query = self._base_query().filter(
                    and_(
                        Transaction.date >= first_day.date(),
                        Transaction.date <= last_day.date(),
                    )
                )

                for db_transaction in db_query:
                    yield self._convert_db_transaction(db_transaction)

            except SQLAlchemyError as e:
                raise BackendError(f"Database month query failed: {e}") from e

        return month_iterator_from_query(month_num, year, self, query)

    def update_record(self, transaction_id: str, updates: dict[str, object]) -> None:
        """Update an existing transaction record.

        Args:
            transaction_id: ID of transaction to update
            updates: Dictionary of fields to update

        Raises:
            DataValidationError: If parameters are invalid
            BackendError: If database operation fails
        """
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            raise DataValidationError("Transaction ID must be a non-empty string")

        if not updates:
            raise DataValidationError("Updates dictionary cannot be empty")

        try:
            db_id = int(transaction_id)

            query = self.session.query(Transaction).filter(
                and_(
                    Transaction.id == db_id,
                    Transaction.account_id == self.account_id,
                )
            )

            db_transaction = query.first()
            if not db_transaction:
                raise DataValidationError(f"Transaction {transaction_id} not found")

            # Apply updates
            for field, value in updates.items():
                if field == "value" and hasattr(value, "cents"):
                    setattr(db_transaction, field, value.cents())
                elif field == "categories" and isinstance(value, list):
                    setattr(db_transaction, field, ",".join(str(cat) for cat in value))
                    # Also update category_membership
                    category_membership: dict[str, bool] = {}
                    for cat in value:
                        if hasattr(cat, "ancestor_names"):
                            for ancestor_name in cat.ancestor_names(include_self=True):
                                category_membership[ancestor_name] = True
                        else:
                            category_membership[str(cat)] = True
                    setattr(db_transaction, "category_membership", category_membership)
                else:
                    setattr(db_transaction, field, value)

            self.session.commit()
            self._logger.debug(f"Updated transaction {transaction_id}")

        except ValueError as e:
            raise DataValidationError(f"Invalid transaction ID format: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Failed to update transaction {transaction_id}: {e}")
            raise BackendError(f"Database update failed: {e}") from e

    def delete_record(self, transaction_id: str) -> None:
        """Delete a transaction record.

        Args:
            transaction_id: ID of transaction to delete

        Raises:
            DataValidationError: If transaction_id is invalid
            BackendError: If database operation fails
        """
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            raise DataValidationError("Transaction ID must be a non-empty string")

        try:
            db_id = int(transaction_id)

            query = self.session.query(Transaction).filter(
                and_(
                    Transaction.id == db_id,
                    Transaction.account_id == self.account_id,
                )
            )

            db_transaction = query.first()
            if not db_transaction:
                raise DataValidationError(f"Transaction {transaction_id} not found")

            self.session.delete(db_transaction)
            self.session.commit()

            self._logger.debug(f"Deleted transaction {transaction_id}")

        except ValueError as e:
            raise DataValidationError(f"Invalid transaction ID format: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Failed to delete transaction {transaction_id}: {e}")
            raise BackendError(f"Database delete failed: {e}") from e

    def get_transaction_count(
        self,
        start_date: Optional[datetime_date] = None,
        end_date: Optional[datetime_date] = None,
    ) -> int:
        """Get count of transactions in date range.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Number of transactions in range

        Raises:
            BackendError: If database operation fails
        """
        try:
            query = self._base_query()

            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)

            count_result = query.count()
            return int(count_result)

        except SQLAlchemyError as e:
            raise BackendError(f"Failed to count transactions: {e}") from e

    def _base_query(self) -> Any:
        """Get base query filtered by account ID.

        Returns:
            SQLAlchemy query object
        """
        return self.session.query(Transaction).filter(
            Transaction.account_id == self.account_id
        )

    def _convert_db_transaction(
        self, db_transaction: Transaction
    ) -> "financespy.transaction.Transaction":
        """Convert database transaction to domain transaction.

        Args:
            db_transaction: Database transaction record

        Returns:
            Domain Transaction object

        Raises:
            BackendError: If conversion fails
        """
        try:
            # Parse categories
            categories = []
            if db_transaction.categories:
                category_names = [
                    name.strip()
                    for name in db_transaction.categories.split(",")
                    if name.strip()
                ]
                categories = [self.categories.category(name) for name in category_names]

            transaction = financespy.transaction.Transaction(
                value=Money(cents=cast(int, db_transaction.value)),
                categories=categories,
                description=cast(str, db_transaction.description) or "",
            )

            transaction.id = str(cast(int, db_transaction.id))
            transaction.date = cast(datetime_date, db_transaction.date)

            return transaction

        except Exception as e:
            raise BackendError(f"Failed to convert database transaction: {e}") from e

    def all_transactions(self) -> list["financespy.transaction.Transaction"]:
        """Get all transactions for this account.

        Returns:
            List of all transactions

        Raises:
            BackendError: If database operation fails
        """
        try:
            query = self._base_query().order_by(Transaction.date.desc())
            return [self._convert_db_transaction(db_trans) for db_trans in query.all()]

        except SQLAlchemyError as e:
            raise BackendError(f"Failed to retrieve all transactions: {e}") from e

    def query_with_predicate(
        self,
        predicate_expression: str,
        start_date: Optional[datetime_date] = None,
        end_date: Optional[datetime_date] = None,
        dialect: Optional[SQLDialect] = None,
    ) -> Iterator["financespy.transaction.Transaction"]:
        """Query transactions using a predicate expression with database-level filtering.

        This method compiles the predicate expression to SQL and executes it directly
        in the database, enabling efficient filtering without loading all records into
        memory.

        Args:
            predicate_expression: Predicate expression string (e.g., "is_groceries AND (NOT is_kaufland)")
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            dialect: SQL dialect override. If None, auto-detects from session.

        Returns:
            Iterator of matching transactions

        Raises:
            BackendError: If database operation fails or predicate is invalid

        Examples:
            >>> for tx in backend.query_with_predicate("is_groceries"):
            ...     print(tx)

            >>> from datetime import date
            >>> txs = list(backend.query_with_predicate(
            ...     "is_restaurant AND (value > 2000)",
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 12, 31)
            ... ))
        """
        try:
            # Auto-detect dialect if not provided
            if dialect is None:
                dialect = self._detect_dialect()

            # Compile predicate to SQL
            compiler = SQLPredicateCompiler(dialect=dialect)
            where_clause = compiler.compile(predicate_expression)

            # Build base query with date filters
            query = self._base_query()

            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)

            # Add predicate filter using raw SQL
            query = query.filter(text(where_clause))

            self._logger.debug(
                f"Executing predicate query: {predicate_expression} -> {where_clause}"
            )

            for db_transaction in query:
                yield self._convert_db_transaction(db_transaction)

        except SQLAlchemyError as e:
            self._logger.error(f"Failed to execute predicate query: {e}")
            raise BackendError(f"Database predicate query failed: {e}") from e
        except Exception as e:
            self._logger.error(f"Error in predicate query: {e}")
            raise BackendError(f"Predicate query failed: {e}") from e

    def _detect_dialect(self) -> SQLDialect:
        """Detect SQL dialect from the session's engine.

        Returns:
            SQL dialect string
        """
        try:
            dialect_name = self.session.bind.dialect.name
            if dialect_name in ("postgresql", "sqlite", "mysql"):
                return dialect_name  # type: ignore
            # Default to postgresql for compatible JSONB syntax
            return "postgresql"
        except Exception:
            return "postgresql"

    def close(self) -> None:
        """Close database session and cleanup resources."""
        try:
            if self.session:
                self.session.close()
            self._logger.info("SQL backend session closed")
        except Exception as e:
            self._logger.error(f"Error closing SQL backend: {e}")

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
        self.close()


class SQLBackendFactory:
    """Factory for creating SQL backends with proper setup."""

    def __init__(self, database_url: str) -> None:
        """Initialize factory with database URL.

        Args:
            database_url: SQLAlchemy database URL

        Raises:
            BackendConnectionError: If database connection fails
        """
        try:
            self.engine = create_engine(database_url)
            self.session_class = sessionmaker(bind=self.engine)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        except Exception as e:
            raise BackendConnectionError(f"Failed to initialize database: {e}") from e

    def create_backend(self, account_id: int, categories: Categories) -> SQLBackend:
        """Create a new SQL backend instance.

        Args:
            account_id: Account ID for the backend
            categories: Category system
            base_class: SQLAlchemy declarative base class

        Returns:
            Configured SQLBackend instance

        Raises:
            BackendConnectionError: If backend creation fails
        """
        try:
            session = self.session_class()

            if categories is None:
                raise BackendConnectionError("Categories must be provided")
            return SQLBackend(account_id, session, categories)

        except Exception as e:
            raise BackendConnectionError(f"Failed to create SQL backend: {e}") from e

    def close(self) -> None:
        """Close database engine."""
        if self.engine:
            self.engine.dispose()
