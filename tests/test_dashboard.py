import random
from datetime import date

from financespy.account import memory_account
from financespy.dashboards import load_dashboard
from financespy.money import ZERO, Money
from financespy.transaction import Transaction
from tests.test_utils import get_categories


def random_account():
    """Creates a random in-memory account for testing purposes"""

    account = memory_account(get_categories())

    years = [2020, 2021, 2022]
    months = list(range(1, 13))
    days = list(range(1, 29))

    categories = account.backend.categories
    cat_list = categories.all

    for year in years:
        for month in months:
            selected_days = sorted(random.sample(days, 15))

            for day in selected_days:
                dt = date(year=year, month=month, day=day)

                value = random.randint(500, 15000)
                random_category = categories.category(random.choice(cat_list))
                record = Transaction(
                    value=Money(cents=value),
                    categories=[random_category],
                    description="",
                )

                account.insert_record(dt, record)

    return account


def test_summary():
    template = """
    template:
        rows:
            - charts:
                - type: table
                  id: overview1
                  formula:
                    columns: sum, cat
                    categories: "main_categories"
                  title: Overview 1
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(
        date_from=date_from, date_to=date_to)
    )

    totals = {}
    cats = account.categories.categories("main_categories")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, account)
    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items()
               ) == set(totals_from_chart.items())


def test_pie():
    template = """
    template:
        rows:
            - charts:
                - type: pie
                  id: overview1
                  formula:
                    categories: "main_categories"
                  title: Overview 1
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(
        date_from=date_from, date_to=date_to))

    totals = {}
    cats = account.categories.categories("main_categories")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, account)
    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items() if v > ZERO) == set(
        totals_from_chart.items()
    )


def test_budget():
    template = """
    template:
      rows:
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
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(
        date_from=date_from, date_to=date_to))

    totals = {}
    cats = account.categories.categories("[food, shopping, body_and_hygiene]")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, account)
    totals_from_chart = {}
    for cat_name, total in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert (
        set((k, v) for k, v in totals.items())
        == set(totals_from_chart.items())
    )


def test_tree():
    template = """
    template:
      rows:
          - charts:
              - type: treemap
                id: overview
                title: Tree Map
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(
        date_from=date_from, date_to=date_to))

    data = dashboard.chart_data(transactions, account)
    print(data)


def test_parameters():
    "Tests charts with supplied parameters"

    values = ["food", "expenses", "shopping"]

    for val in values:
        aux_test_parameters(val)


def aux_test_parameters(param_val):
    """
    Creates a random account and load a summary dashboard with a
    supplied parameter map
    """

    template = """
    template:
        parameters:
            - type: category
              name: selected_cat
              label: "Selected category"
              default: expenses

        rows:
            - charts:
                - type: pie
                  id: overview
                  title: Overview
                  formula:
                    categories: $selected_cat.children
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(
        account.transactions(
            date_from=date_from,
            date_to=date_to
        )
    )

    totals = {}
    cats = account.categories.categories(f"{param_val}.children")
    for cat in cats:
        totals[cat.name] = ZERO
    for t in transactions:
        for cat in cats:
            if t.matches_category(cat):
                totals[cat.name] += t.value
                break

    data = dashboard.chart_data(transactions, account, {
                                "selected_cat": param_val})

    totals_from_chart = {}
    for total, cat_name in data[0]["data"]:
        totals_from_chart[cat_name] = Money(cents=total)

    assert set((k, v) for k, v in totals.items() if v > ZERO) == set(
        totals_from_chart.items()
    )
