from datetime import date
from financespy.account import open_account
from financespy.transaction import Transaction
from financespy.money import Money
import sys
import random

account = open_account("/home/danilo/Documents/Finances/accounts/" + sys.argv[1])

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
