"""
This module hosts the Chart type and supporting functions for extracting
chart data, based on the chart type, filters, and parameters (transactions
and parameter map)
"""
from collections import defaultdict
from pydantic import BaseModel, Field
from typing import Any
from .formula import Formula
from .reducers import CategoryReducer, new_reducer
from .treemap import tree_map


def reducers(columns, cat):
    """
    Returns a list reducer objects for a list of columns (cat, sum, count,
    etc.),

    When a list of transactions is processed, each transaction is matched
    to a single row, and the transaction value is submitted to all reducers
    of the row. The CategoryReducer object has the function of output the
    category name in the row.

    Ex:
    Columns: cat, sum, count

    Rows:
    [[travel, 100.0, 5],
     [food, 340, 6]]
    """
    result = []

    for col in columns:
        if col in ["cat", "category"]:
            result.append(CategoryReducer(cat))
            continue
        result.append(new_reducer(col))

    return result


def result_row(row):
    "Returns the final values collecteds by each reducer of a row"

    return [reducer.total() for reducer in row]


def summary_function(formula, transactions, categories, params):
    """
    Generic chart function that takes a list of transactions, groups them by
    categories, and produces a summary for each group. The list of categories
    is given by the formula parameter.
    """
    category_list = formula.category_list(categories, params)
    columns = formula.columns

    result = {cat.name: reducers(columns, cat.name) for cat in category_list}

    for trans in transactions:
        category = None
        for cat in category_list:
            if trans.matches_category(cat):
                category = cat
                break

        if not category:
            continue

        row = result[category.name]

        for reducer in row:
            reducer.add(trans.value)

    return [result_row(row) for row in result.values()]


def pie_chart_data(formula, transactions, categories, params):
    """Chart function for Pie charts, filter empty categories by default"""

    rows = summary_function(formula, transactions, categories, params)

    return [(val, cat) for val, cat in rows if val > 0]


def budget_chart_formula(chart):
    return Formula(
        columns=["cat", "sum"],
        categories=[key for key, val in chart.properties["budgets"].items()],
        categories_exclude=[],
        filter_string="",
    )


# Maps a chart type to a chart function
functions = defaultdict(lambda: summary_function, treemap=tree_map, pie=pie_chart_data)

# Maps a chart object to its corresponding Formula object
chart_to_formula = defaultdict(
    lambda: (lambda c: c.formula),
    budget=budget_chart_formula,
)


class Chart(BaseModel):
    """
    Defines the chart type.
    """

    chart_id: str = Field(alias="id", serialization_alias="id")
    title: str = ""
    size: str = ""
    chart_type: str = Field(alias="type", serialization_alias="type")
    formula: Formula | None = Formula()
    columns: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)

    def chart_data(self, transactions, account, params):
        """ "
        Processes a stream of transaction and gives output chart
        data to be plotted
        """
        chart_data_function = functions[self.chart_type]
        formula_function = chart_to_formula[self.chart_type]

        formula = formula_function(self)

        return {
            "id": self.chart_id,
            "data": chart_data_function(
                formula=formula,
                transactions=transactions,
                categories=account.categories,
                params=params,
            ),
        }
