"""
Main submodule of financespy.dashboard module. Contains the Dashboard type
and functions to load structured data (from json/yaml) to a Dashboard object
"""
from typing import List
import yaml
from pydantic import BaseModel, Field
from .charts import Chart
from .formula import Formula


def open_file(file_name):
    """
    Loads a dashboard from a YAML file
    """

    with open(file_name, "r", encoding="utf8") as yaml_file:
        return Dashboard(**yaml.safe_load(yaml_file))


def load_dashboard(value):
    "Auxiliary function to load a dashboard file"
    values = yaml.safe_load(value)
    return Dashboard(**values)


def get_list(dict_, key, default_val=()):
    """Converts a string field from a dictionary into a list"""

    result = [elem.strip() for elem in dict_.get(key, "").split(",") if elem.strip()]

    if not result:
        return default_val

    return result


class Row(BaseModel):
    """
    Represents a collection of charts that should
    be displayed in the same row
    """

    charts: List[Chart]


class Parameter(BaseModel):
    """
    Defines a parameter belonging to a chart.
    """

    name: str = ""
    param_type: str = Field(default="", alias="type", serialization_alias="type")
    default: str = ""


class Dashboard(BaseModel):
    """
    Defines a custom dashboard, composed of a series of rows,
    each row containing one or more charts
    """

    template: list[Row] = Field(default_factory=list)
    parameters: list[Parameter] = Field(default_factory=list)
    account: str = ""

    @property
    def charts(self):
        """
        Returns a map of chart-id -> chart
        """
        charts = {}
        for row in self.template:
            for chart in row.charts:
                charts[chart.chart_id] = chart

        return charts

    def chart_data(self, transactions, account, params={}):
        """
        Returns the numerical data needed to plot every chart of the dashboard
        """
        transactions = list(transactions)

        return [
            chart.chart_data(transactions, account, params)
            for chart in self.charts.values()
        ]
