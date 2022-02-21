from dataclasses import dataclass, field
from typing import List, Tuple
import ast
import _ast


@dataclass
class Formula:
    columns: List[Tuple[str]]
    generator_expr: str
    variable: str
    filter_expr: str

    @property
    def filter_function(self):
        return eval(self.filter_expr)

    def apply_parameters(self, params):
        if not params:
            return self

        gen_exp = self.generator_expr

        for k, v in params.items():
            gen_exp = gen_exp.replace(f"params.{k}", v)

        return Formula(
            columns=self.columns,
            generator_expr=gen_exp,
            variable=self.variable,
            filter_expr=self.filter_expr,
        )


def parse_value(val):
    if type(val) is _ast.Name:
        return (val.id,)

    if type(val) is _ast.Call:
        return val.func.id, val.args[0].id


def parse_columns(expr_ast):
    return [parse_value(val) for val in expr_ast.body.elt.elts]


def parse_variable(expr_ast):
    return expr_ast.body.generators[0].target.id


def parse_generator(expr_ast):
    return expr_ast.body.generators[0].iter.id


def parse_filter_expr(expr_ast):
    return None


def parse_formula(formula):
    values, remainder = formula.split("for")
    formula = f"( ({values}) for {remainder} )"
    expr_ast = ast.parse(formula, mode="eval")

    return Formula(
        columns=parse_columns(expr_ast),
        generator_expr=parse_generator(expr_ast),
        variable=parse_variable(expr_ast),
        filter_expr=parse_filter_expr(expr_ast),
    )


def default_formula(chart):
    return parse_formula(chart.formula_str)


def parse_budget(chart):
    columns = [("cat",), ("sum",)]
    generator = ",".join(chart.properties["budgets"].keys())
    variable = "cat"
    filter_expr = ""

    return Formula(
        columns=columns,
        generator_expr=f"[{generator}]",
        variable=variable,
        filter_expr=filter_expr,
    )


formulas = {"budget": parse_budget, "treemap": lambda c: None}


def get_formula(chart):
    return formulas.get(chart.chart_type, default_formula)
