from datetime import date
from financespy.dashboards import load_dashboard
from tests.test_dashboard import random_account


def test_tree_with_formula():
    template = """
    template:
      rows:
          - charts:
              - type: treemap
                id: overview
                title: Tree Map
                formula:
                  categories: shopping, food
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(date_from=date_from, date_to=date_to))

    data = dashboard.chart_data(transactions, account)
    print(data)


def test_tree_with_params():
    template1 = """
    template:
      rows:
          - charts:
              - type: treemap
                id: overview
                title: Tree Map
                formula:
                  categories: $cat1, $cat2
    """
    dashboard1 = load_dashboard(template1)

    template2 = """
    template:
      rows:
          - charts:
              - type: treemap
                id: overview
                title: Tree Map
                formula:
                  categories: shopping, food
    """
    dashboard2 = load_dashboard(template2)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(date_from=date_from, date_to=date_to))

    data1 = dashboard1.chart_data(
        transactions, account, params={"cat1": "shopping", "cat2": "food"}
    )
    data2 = dashboard2.chart_data(transactions, account)

    assert data1 == data2
