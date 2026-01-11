FinancesPy Documentation
========================

FinancesPy is a Python API for personal finance management inspired by GnuCash, Mint, and YNAB.
It provides a literate API for personal finance concepts with support for multiple storage backends
and hierarchical transaction categorization.

Features
--------

* **Multiple Storage Backends**: Support for in-memory, CSV files, XLSX files, SQL databases, and GnuCash files
* **Hierarchical Categories**: Tree-structured categorization system with inheritance
* **Type Safety**: Full type hints throughout the codebase
* **Extensible Design**: Pluggable backend architecture
* **Professional Tooling**: Pre-commit hooks, CI/CD, and comprehensive testing

Quick Start
-----------

.. code-block:: python

    from financespy import Money, Transaction, MemoryBackend

    # Create a transaction
    transaction = Transaction(
        value=Money(50.00),
        description="Groceries",
        categories=["food", "groceries"]
    )

    # Use a backend to store transactions
    backend = MemoryBackend()
    backend.insert_record(datetime.now().date(), transaction)

Installation
------------

.. code-block:: bash

    pip install financespy

For development:

.. code-block:: bash

    pip install -e ".[dev]"

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/core
   api/backends
   api/charting
   api/exceptions

Core Modules
~~~~~~~~~~~~

.. automodule:: financespy
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`