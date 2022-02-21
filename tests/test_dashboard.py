import random
from datetime import date
from tests.test_utils import get_categories
from financespy.account import memory_account
from financespy.transaction import Transaction
from financespy.money import Money, ZERO
from financespy.dashboards import load_dashboard


def random_account():
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
                    value=Money(cents=value), categories=[random_category], description=""
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
                  formula: "sum, cat for cat in main_categories"
                  title: Overview 1
    """
    dashboard = load_dashboard(template)
    account = random_account()

    date_from = date(year=2021, month=1, day=28)
    date_to = date(year=2021, month=5, day=28)

    transactions = list(account.transactions(date_from=date_from, date_to=date_to))

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

    assert set((k, v) for k, v in totals.items() if v > ZERO) == set(totals_from_chart.items())
