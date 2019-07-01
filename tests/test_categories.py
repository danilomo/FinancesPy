import pytest

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

def test_undefined():
    cats = get_categories()
    undefined_cat = cats.category("church_tax")
    assert undefined_cat.name == "uncategorized"

def test_matches():
    cats = get_categories()
    lidl = cats.category("lidl")
    aldi = cats.category("aldi")
    groceries = cats.category("groceries")
    food = cats.category("food")
    tax = cats.category("tax")

    assert not lidl.matches(aldi)
    assert not aldi.matches(lidl)
    assert aldi.matches(groceries)
    assert not groceries.matches(aldi)
    assert aldi.matches(food)
    assert groceries.matches(food)
    assert not tax.matches(cats.category("food"))
