import pytest

import datetime
from financespy import categories
from financespy.transaction import parse_transaction
from financespy.transaction import Transaction
from financespy.memory_backend import MemoryBackend

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

def test_parse_string():
    mb = MemoryBackend(get_categories())
    mb.insert_record(
        dt(10, 2),
        "10, food"
    )

    assert mb.records(dt(10,2))[0].value._cents == 1000
    assert mb.records(dt(10,2))[0].description == "food"

def test_insert_transaction_object():
    mb = MemoryBackend(get_categories())
    mb.insert_record(
        dt(10, 2),
        parse_transaction("149, groceries", get_categories())
    )

    assert mb.records(dt(10,2))[0].value._cents == 14900
    assert mb.records(dt(10,2))[0].description == "groceries"

def test_invalid_type():
    mb = MemoryBackend(get_categories())
    
    with pytest.raises(TypeError):
        mb.insert_record(dt(10,2), (100, "food"))
