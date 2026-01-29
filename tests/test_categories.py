from financespy import categories
from financespy.transaction import parse_transaction


def get_categories():
    default_categories = [
        {
            "expenses": [
                {"others": ["uncategorized", "withdrawal", "misc"]},
                {"church": ["tithes", "offering"]},
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
                                "asia",
                            ]
                        },
                        "restaurant",
                        "street_food",
                        "kfc",
                        "hamburguer",
                        "icecream",
                        "mc",
                        "sushi",
                        "bk",
                    ]
                },
                {"utilities": ["internet", "electricity", "cellphone_balance"]},
                {"travel": ["plane_ticket", "hotel_reservation", "train_ticket"]},
                {"tax": ["tv_tax"]},
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
                        "moemax",
                    ]
                },
                {
                    "education": [
                        {"course_fee": ["german_course", "inlingua", "vhs"]},
                        "textbook",
                        "school_supplies",
                        "magazine",
                        "book",
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
                        "müller",
                    ]
                },
                {
                    "commuting": [
                        "monthly_ticket",
                        "day_ticket",
                        "single_ticket",
                        "bus_ticket",
                    ]
                },
            ]
        }
    ]

    return categories.categories_from_list(default_categories)


def test_undefined():
    cats = get_categories()
    undefined_cat = cats.category("church_tax")
    assert undefined_cat.name == "uncategorized"


def test_category_matches():
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


def test_transaction_matching():
    cats = get_categories()
    t1 = parse_transaction("100, aldi", cats)
    t2 = parse_transaction("14,street_food", cats)
    t3 = parse_transaction("500,tax", cats)

    assert t1.is_aldi
    assert not t1.is_edeka
    assert t1.is_groceries
    assert t1.is_food

    assert t2.is_street_food
    assert not t2.is_groceries
    assert t2.is_food

    assert t3.is_tax
    assert not t3.is_food
    assert not t3.is_groceries


def test_category_ancestors():
    """Test the ancestors() method on Category."""
    cats = get_categories()
    lidl = cats.category("lidl")

    # lidl -> groceries -> food -> expenses
    ancestors = lidl.ancestors(include_self=True)
    ancestor_names = [cat.name for cat in ancestors]

    assert ancestor_names == ["lidl", "groceries", "food", "expenses"]


def test_category_ancestors_without_self():
    """Test ancestors() excluding self."""
    cats = get_categories()
    lidl = cats.category("lidl")

    ancestors = lidl.ancestors(include_self=False)
    ancestor_names = [cat.name for cat in ancestors]

    assert ancestor_names == ["groceries", "food", "expenses"]


def test_category_ancestor_names():
    """Test the ancestor_names() convenience method."""
    cats = get_categories()
    aldi = cats.category("aldi")

    names = aldi.ancestor_names(include_self=True)
    assert names == ["aldi", "groceries", "food", "expenses"]


def test_root_category_ancestors():
    """Test ancestors on a root category (no parent)."""
    cats = get_categories()
    expenses = cats.category("expenses")

    ancestors = expenses.ancestors(include_self=True)
    assert len(ancestors) == 1
    assert ancestors[0].name == "expenses"

    ancestors_without_self = expenses.ancestors(include_self=False)
    assert len(ancestors_without_self) == 0
