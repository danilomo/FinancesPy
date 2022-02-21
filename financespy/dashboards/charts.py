from .reducers import new_reducer
from .treemap import tree_map
from .formula import get_formula, Formula
from dataclasses import dataclass, field
from financespy.money import ZERO


def summary_function(formula, transactions, account, ignore_zero=True):
    categories = account.backend.categories
    categories_list = categories.categories(formula.generator_expr)
    columns = formula.columns
    variable = formula.variable

    rows = []

    for cat in categories_list:
        reducers = {}

        for (col,) in columns:
            if col == variable:
                continue

            reducer = new_reducer(col)
            reducers[col] = reducer

        for transaction in transactions:
            if not transaction.matches_category(cat):
                continue

            for reducer in reducers.values():
                reducer.add(transaction.value)

        row = []
        ignore = False

        for (col,) in columns:
            if col == variable:
                row.append(str(cat))
                continue

            total = reducers[col].total()
            if total == ZERO and ignore_zero:
                ignore = True

            row.append(int(total._cents))

        if ignore:
            continue

        rows.append(row)

    return rows


def budget_function(formula, transactions, account):
    return summary_function(formula, transactions, account, ignore_zero=False)


functions = {
    "pie": summary_function,
    "table": summary_function,
    "sankey": None,
    "budget": budget_function,
    "treemap": tree_map,
}


def chart_data(chart, transactions, account, params):
    chart_data_function = functions.get(chart.chart_type, None)

    if not chart_data_function:
        raise Exception(f"Invalid chart type {chart.chart_type}")

    formula = chart.formula

    return chart_data_function(formula, transactions, account)


@dataclass
class Chart:
    chart_id: str
    title: str
    size: str
    chart_type: str
    formula_str: str = ""
    columns: str = ""
    properties: dict = field(default_factory=dict)

    @property
    def formula(self):
        formula = get_formula(self)
        return formula(self)

    def chart_data(self, transactions, account, params):
        return {
            "id": self.chart_id,
            "data": chart_data(self, transactions, account, params),
        }

    @property
    def layout(self):
        return {
            "id": self.chart_id,
            "formula": self.formula_str,
            "title": self.title,
            "size": self.size,
            "type": self.chart_type,
            "columns": self.columns,
            "properties": self.properties,
        }
