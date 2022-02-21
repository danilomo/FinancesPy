from dataclasses import dataclass, field
from typing import List, Tuple
import yaml
from .charts import Chart


def open_file(file_name):
    with open(file_name, "r") as yaml_file:
        return parse_map_as_dashboard(yaml.safe_load(yaml_file))


def load_dashboard(value):
    return parse_map_as_dashboard(yaml.safe_load(value))


def parse_map_as_dashboard(obj):
    template = obj.get("template", {})

    rows = []
    parameters = []

    for row in template.get("rows", []):
        charts = []

        for chart in row.get("charts", []):
            charts.append(
                Chart(
                    chart_id=chart["id"],
                    formula_str=chart.get("formula", ""),
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
    charts: List[Chart]

    @property
    def layout(self):
        return [chart.layout for chart in self.charts]


@dataclass
class Parameter:
    name: str = ""
    param_type: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.param_type,
            "properties": self.properties,
        }


@dataclass
class Dashboard:
    rows: List[Row]
    parameters: List[Parameter]

    @property
    def charts(self):
        charts = {}
        for row in self.rows:
            for chart in row.charts:
                charts[chart.chart_id] = chart

        return charts

    def chart_data(self, transactions, account, params=None):
        transactions = list(transactions)

        return [
            chart.chart_data(transactions, account, params)
            for chart in self.charts.values()
        ]

    @property
    def layout(self):
        return [row.layout for row in self.rows]

    def to_dict(self):
        return {
            "layout": self.layout,
            "parameters": [param.to_dict() for param in self.parameters],
        }


@dataclass
class Formula:
    columns: List[Tuple[str]]
    generator_expr: str
    variable: str
    filter_expr: str

    @property
    def filter_function(self):
        return eval(self.filter_expr)
