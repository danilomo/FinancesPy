"""
Main submodule of financespy.dashboard module. Contains the Dashboard type
and functions to load structured data (from json/yaml) to a Dashboard object
"""

from dataclasses import dataclass, field
from typing import List

import yaml

from .charts import Chart
from .formula import Formula


def open_file(file_name):
    """
    Loads a dashboard from a YAML file
    """

    with open(file_name, "r", encoding="utf8") as yaml_file:
        return parse_map_as_dashboard(yaml.safe_load(yaml_file))


def load_dashboard(value):
    "Auxiliary function to load a dashboard file"

    return parse_map_as_dashboard(yaml.safe_load(value))


def get_list(dict_, key, default_val=()):
    """Converts a string field from a dictionary into a list"""

    result = [elem.strip() for elem in dict_.get(
        key, "").split(",") if elem.strip()]

    if not result:
        return default_val

    return result


def parse_map_as_dashboard(obj):
    """
    Converts a python dictionary into a Dashboard object
    """

    template = obj.get("template", {})

    rows = []
    parameters = []

    for row in template.get("rows", []):
        charts = []

        for chart in row.get("charts", []):
            formula_dict = chart.get("formula", {})
            formula = Formula(
                columns=get_list(
                    formula_dict,
                    "columns",
                    ["sum", "cat"]
                ),
                categories=get_list(
                    formula_dict,
                    "categories",
                    ["main_categories"]
                ),
                categories_exclude=get_list(
                    formula_dict,
                    "categories_exclude"
                ),
                filter_string=formula_dict.get("filter_expr", ""),
            )
            charts.append(
                Chart(
                    chart_id=chart["id"],
                    formula=formula,
                    title=chart["title"],
                    chart_type=chart["type"],
                    size=chart.get("size", "medium"),
                    columns=chart.get("columns", ""),
                    properties=chart.get("properties", {}),
                )
            )

        rows.append(Row(charts))

    for param in template.get("parameters", []):
        properties = param.get("properties", {})
        param_type = param.get("type", "")
        name = param.get("name", "")

        parameters.append(
            Parameter(name=name, param_type=param_type, properties=properties)
        )

    return Dashboard(rows, parameters)


@dataclass
class Row:
    """
    Represents a collection of charts that should
    be displayed in the same row
    """
    charts: List[Chart]

    @property
    def layout(self):
        "Returns the layout of the row"
        return [chart.layout for chart in self.charts]


@dataclass
class Parameter:
    """
    Defines a parameter belonging to a chart.
    """
    name: str = ""
    param_type: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        "Returns a map structure describing the parameter"
        return {
            "name": self.name,
            "type": self.param_type,
            "properties": self.properties,
        }


@dataclass
class Dashboard:
    """
    Defines a custom dashboard, composed of a series of rows,
    each row containing one or more charts
    """
    rows: List[Row]
    parameters: List[Parameter]

    @property
    def charts(self):
        """
        Returns a map of chart-id -> chart
        """
        charts = {}
        for row in self.rows:
            for chart in row.charts:
                charts[chart.chart_id] = chart

        return charts

    def chart_data(self, transactions, account, params=None):
        """
        Returns the numerical data needed to plot every chart of the dashboard
        """
        transactions = list(transactions)

        return [
            chart.chart_data(transactions, account, params)
            for chart in self.charts.values()
        ]

    @property
    def layout(self):
        """
        Returns an object that describes the layout of the dashboard
        """
        return [row.layout for row in self.rows]

    def to_dict(self):
        """
        Returns the recipe of the dashboard: its layout and accepted parameters
        """
        return {
            "layout": self.layout,
            "parameters": [param.to_dict() for param in self.parameters],
        }
