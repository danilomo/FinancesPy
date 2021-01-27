# FinancesPy

FinancesPy is an API for personal finances inspired by Gnucash, Mint, Ynab, and similar software. It provides:

* A literate API for personal finances concepts that can be used in any Python application.
* Support for multiple storage (called backends in the project): comma-separated-values files, XLSX files, relational, and relational databases.
* Importing and exporting from one storage type to another.
* Time iterators for querying transactions by months, weeks, or days.
* Hierarchical categorization of transactions (e.g.: food -> groceries -> [aldi, rewe, penny, ...])

It does not provide:

* A user interface. Those will be provided in separate projects: [FinancesPy-CLI](https://github.com/danilomo/FinancesPy-CLI), [FinancesPy-Web](https://github.com/danilomo/FinancesPy-Web)

However, FinancesPy is usable out of the box with Jupyter notebooks. Some examples will be available in this repository.

## Categories

Categories are just labels you put on your transactions according to the source or destination of the money. The concept
appears at virtually any other software of the genre. FinancesPy has two distinct features in this regard:

* Multiples categories can be assigned to a transaction. Every transaction should have a main category, additional categories
  are optional
* Categories are hierarchical. A category can form a "tree" (in CS sense) of categories, for example:
    * food
        * restaurant
        * junk_food
        * bakery
        * icecream
        * ...
        * groceries
            * aldi
            * edeka
            * penny

In the example above, you have a super-category "food" for every euro/dollar/rupee you spend to the purpose of feeding yourself.
If you mark a transaction with the category "penny", it is also belongs to the "groceries" and "food" categories.
Having this hierarchical labeling system allows precise queries being made over the records:

* How much did I spend in penny and aldi: ```penny and aldi```
* How much did I spend eating outside: ```food and (not groceries)```
* How much did I spend eating outside with my girlfriend: ```food and (not groceries) and gilrfriend```. In this example you
combine having multiple labels with hierarchical labeling.
  
Looks overkill, I know, but I found this concept useful for my own financial tracking. It's nice being able to visualize
my spending in multiple ways. You also don't need to abuse this system if you don't need/want to.

Categories are best represented in the same way identifiers are represented in a programming language: no spaces in between.
You can follow snake or camel-case conventions to express multi-word concepts. If follow this convention, then you can use the magic
method "is_<something>" in the class transaction.

```
march_records = ...
groceries_march = [ trans for trans in march_records if trans.is_groceries ]
```

If you don't follow this convention, the method "matches_category" should be used instead:

```
march_records = ...
junk_food_march = [ trans for trans in march_records if trans.matches_category("junk food") ]
```

The boolean queries mentioned above look more pretty if you use this convention.

## Backends

"Backend" refers to the storage medium/file/database/etc on which the transactions are stored. The following list describes the supported backends at time of writing:

### In memory

A volatile storage of transaction records. It uses Python maps and lists internally, and it provides all time iterators
for querying months, weeks and days. This backend is used for two purposes:

* For the unit/integration tests in the project
* For exporting data from other backends (the SQL backend uses it internally, for instance)

```
categories = categories_from_list([
...
])

be = MemoryBackend(categories)

transaction = parse_transaction("97.2, monthly_ticket")
be.insert_record(date=datetime(10, 12, 2020), transaction))
```

### Comma separated files

This is a persistent backend that uses just plain text files to store the transaction data. To create a backend object
that uses CSV files, you have to point to the root folder which the files are stored:

```
csv_backend = FilesystemBackend(categories, "/home/john/Documents/finance/savings")
```

The subfolders and files should be written according to the following conventions:

* There should be a folder for each year, if there are recordings for this year. The folder name is the year with all digits
  ("2019", "2020", "2021", etc.)
* Inside the folder for each year, there should be a folder for each month, and they are named with the three initial letters
of the english name of the month: jan, feb, mar, ...
* For each day which has recordings, you append transactions in a csv file named: \<day number\>.csv (starts with 1)
* Each line in the CSV has the following format (elements inside \[\] are optional):
    * \<value\>, \<main_category\>, \[description\], \[additional categories separated by a comma\]

### XLSX files

Using Excel is the most common form of tracking spending with a computer. The XLSXBackend class allows to use Excel spreadsheets
as a backend for FinancesPy. It is also necessary to follow a certain convention so FinancesPy can know how to read the 
spreadsheet. The picture below shows an Excel spreadsheet adapted for FinancesPy:

![alt text](https://raw.githubusercontent.com/danilomo/FinancesPy/master/.github/screenshot_libreofficecalc.png)

You can use any font, cell colors, etc. FinancesPy will just enforce the following conventions:

* A XLSX backend is represented by a folder that contains XLSX files. Each file represents a year, and it is named: <year>.xlsx
* There should be a sheet for each month, and they can have any name, but it's better to name them: jan, feb, mar, ...
* Each sheet has the following layout:
    * First column is the day number for the record
    * Second column is the main category
    * Third column is the value
    * Fourth column is a description (optional)
    * Fifth column are additional categories, separated by comma (optional)
    
An example of such spreadsheet can be found here, and a blank template is available here. 

### SQL backend

For using FinancesPy in a larger and multi-user application, using relational databases is the best way. SQLAlchemy is 
used for being independent of database. Check the [source file](https://github.com/danilomo/FinancesPy/blob/master/financespy/sql_backend.py) of the SQLBackend class to inspect the table structure 
and verify which  column types should be used for your favorite database.
