from datetime import date
from financespy.account import open_account
from financespy.dashboards import open_dashboard
import sys

account = open_account("/home/danilo/Documents/Finances/accounts/savings")
dashb = open_dashboard(
    "/home/danilo/Documents/Finances/dashboards/monthly_dashboard.yaml"
)

transactions = list(
    account.transactions(
        date_from=date(year=2020, month=1, day=1),
        date_to=date(year=2020, month=2, day=1),
    )
)

print(transactions)

"""
cat = account.backend.categories.category(sys.argv[1])

chartd = dashb.chart_data(transactions, account)[0]["data"]

for t in transactions:
    if not t.matches_category(cat):
        continue
    print(t)

print("-------")

for row in chartd:
    print(row)
"""

# iter_variable = expr_ast.body.generators[0].iter.id

# return f"lambda {iter_variable}: {filter_exp}"
