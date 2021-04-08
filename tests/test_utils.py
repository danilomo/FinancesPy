import datetime

from financespy import categories
from financespy.transaction import parse_transaction

def get_categories():

    default_categories = [
        "misc",
        "uncategorized",
        {"food": [
            {"groceries": ["lidl", "aldi", "edeka", "rewe"]},
            "restaurant",
            "street_food"
        ]},
        {"utilities": ["internet", "electricity", "cellphone_balance"]},
        {"travel": ["plane_ticket", "hotel_reservation", "train_ticket"]},
        {"tax": ["tv_tax"]},
        {"shopping": ["electronics", "clothing", "sports", "home_goods",
                      "furniture", "shopping_misc", "shoes", "purses", "jewlery"]},
        {"education": [{"course_fee": ["german_course"]}, "textbook", "school_supplies"]},
        {"body_and_hygiene": ["perfume", "hair_product", "hairdresser", "nails"]},
        {"commuting": ["monthly_ticket", "day_ticket", "single_ticket"]}
    ]

    return categories.categories_from_list(default_categories)

def dt(day, month, year = 2019):
    return datetime.date(
        day = day,
        month = month,
        year = year
    )

def parse_date(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats, records_):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [
        (parse_date(date), parse_transaction(trans, cats))
        for date, trans in recs
    ]


def total_iterator(iterator):
    weeks = [
        sum(t.value for t in element.records()) for element in iterator
    ]

    return weeks
