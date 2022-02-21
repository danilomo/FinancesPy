import datetime

from financespy import categories
from financespy.transaction import parse_transaction


default_categories = [
    {
        "expenses": [
            {
                "others": [
                    "uncategorized",
                    "withdrawal",
                    "misc"
                ]
            },
            {
                "church": [
                    "tithes",
                    "offering"
                ]
            },
            {
                "food": [
                    {
                        "groceries": [
                            "lidl",
                            "aldi",
                            "edeka",
                            "asia_market",
                            "alnatura",
                            "rewe",
                            "netto",
                            "penny",
                            "rossmann",
                            "yaz",
                            "nahkauf",
                            "bakery",
                            "backery",
                            "asia"
                        ]
                    },
                    "restaurant",
                    "street_food",
                    "kfc",
                    "hamburguer",
                    "icecream",
                    "mc",
                    "sushi",
                    "bk"
                ]
            },
            {
                "utilities": [
                    "internet",
                    "electricity",
                    "cellphone_balance"
                ]
            },
            {
                "travel": [
                    "plane_ticket",
                    "hotel_reservation",
                    "train_ticket"
                ]
            },
            {
                "tax": [
                    "tv_tax"
                ]
            },
            {
                "shopping": [
                    "saturn",
                    "electronics",
                    "clothing",
                    "sports",
                    "tkmax",
                    "h_m",
                    "kaufhoff",
                    "furniture",
                    "shopping_misc",
                    "shoes",
                    "tedi",
                    "purses",
                    "jewlery",
                    "home_goods",
                    "action",
                    "real",
                    "clothes",
                    "moemax"
                ]
            },
            {
                "education": [
                    {
                        "course_fee": [
                            "german_course",
                            "inlingua",
                            "vhs"
                        ]
                    },
                    "textbook",
                    "school_supplies",
                    "magazine",
                    "book"
                ]
            },
            {
                "body_and_hygiene": [
                    "dm",
                    "perfume",
                    "hair_product",
                    "apotheke",
                    "mueller",
                    "douglas",
                    "hairdresser",
                    "nails",
                    "müller"
                ]
            },
            {
                "commuting": [
                    "monthly_ticket",
                    "day_ticket",
                    "single_ticket",
                    "bus_ticket"
                ]
            }
        ]
    }
]




def get_categories_as_list():
    return default_categories


def get_categories():
    return categories.categories_from_list(default_categories)


def dt(day, month, year=2019):
    return datetime.date(day=day, month=month, year=year)


def parse_date(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d").date()


def records(cats, records_):
    recs = (tuple(line.split(";")) for line in records_.split("\n"))
    return [(parse_date(date), parse_transaction(trans, cats)) for date, trans in recs]


def total_iterator(iterator):
    weeks = [sum(t.value for t in element.records()) for element in iterator]

    return weeks
