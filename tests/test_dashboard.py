from datetime import date
from financespy.dashboards import load_dashboard
from financespy.money import ZERO, Money
from financespy.transaction import Transaction
import pytest


def test_summary(random_account):
    template = """
    template:
        - charts:
            - type: table
              id: overview1
              formula:
                columns: ['sum', 'cat']
                categories: ['main_categories'] 
              title: Overview 1
    """
    dashboard = load_dashboard(template)

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(random_account.transactions(date_from=date_from, date_to=date_to))

    totals = {}
    cats = random_account.categories.categories("main_categories")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, random_account)
    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items()) == set(totals_from_chart.items())


def test_pie(random_account):
    template = """
template:
  - charts:
      - type: pie
        id: overview1
        formula:
          categories: ["main_categories"]
        title: Overview 1
    """
    dashboard = load_dashboard(template)

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(random_account.transactions(date_from=date_from, date_to=date_to))

    totals = {}
    cats = random_account.categories.categories("main_categories")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, random_account)
    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items() if v > ZERO) == set(
        totals_from_chart.items()
    )


def test_budget(random_account):
    template = """
template:
  - charts:
      - type: budget
        id: overview
        title: Monthly budget
        properties:
          budgets:
            food: 450
            shopping: 700
            body_and_hygiene: 100
    """
    dashboard = load_dashboard(template)

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(random_account.transactions(date_from=date_from, date_to=date_to))

    totals = {}
    cats = random_account.categories.categories("[food, shopping, body_and_hygiene]")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, random_account)
    totals_from_chart = {}
    for cat_name, total in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items()) == set(totals_from_chart.items())


def test_tree(random_account):
    template = """
template:
  - charts:
      - type: treemap
        id: overview
        title: Tree Map
    """
    dashboard = load_dashboard(template)
    print(dashboard)

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(random_account.transactions(date_from=date_from, date_to=date_to))

    data = dashboard.chart_data(transactions, random_account)
    print(data)


@pytest.mark.parametrize("param_val", ["food", "expenses", "shopping"])
def test_parameters(random_account, param_val):
    """
    Creates a random account and load a summary dashboard with a
    supplied parameter map
    """
    template = """
parameters:
  selected_cat:
      type: category
      name: selected_cat
      label: "Selected category"
      default: expenses
template:
  - charts:
      - type: pie
        id: overview
        title: Overview
        formula:
          categories: ["$selected_cat.children"]
    """
    dashboard = load_dashboard(template)

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(random_account.transactions(date_from=date_from, date_to=date_to))

    totals = {}
    cats = random_account.categories.categories(f"{param_val}.children")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, random_account, {"selected_cat": param_val})

    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items() if v > ZERO) == set(
        totals_from_chart.items()
    )
