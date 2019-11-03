import datetime
from financespy import categories

def get_categories():
    default_categories = [
        "misc",
        "uncategorized",
        ("food", [ ("groceries", ["lidl", "aldi", "edeka", "rewe"]), "restaurant", "street_food"]),
        ("utilities", ["internet", "electricity", "cellphone_balance"]),
        ("travel", ["plane_ticket", "hotel_reservation", "train_ticket"]),
        ("tax", ["tv_tax"]),
        ("shopping", ["electronics", "clothing", "sports", "home_goods", "furniture", "shopping_misc", "shoes", "purses", "jewlery"]),
        ("education", [("course_fee", ["german_course"]), "textbook", "school_supplies"]),
        ("body_and_hygiene", ["perfume", "hair_product", "hairdresser", "nails"]),
        ("commuting", ["monthly_ticket", "day_ticket", "single_ticket"])        
    ]

    return categories.categories_from_list(default_categories)

def dt(day, month, year = 2019):
    return datetime.date(
        day = day,
        month = month,
        year = year
    )
