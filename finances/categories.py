import sys

_categories = {}
_instances = {}

def get_category( str_ ):
    str_ = str_.lower()

    if str_ not in _categories or "uncategorized" == str_:
        return _uncategorized

    category = _categories[str_]

    if str_ not in _instances:
        _instances[str_] = category()

    return _instances[str_]



class CategoryMeta(type):
    def __init__(cls, name, parents, dct):
        _categories[name.lower()] = cls

        if hasattr( cls, "subtypes" ):
            for subtype in cls.subtypes:
                globals()[subtype] = type(subtype, (cls,), {'subtypes' : []})

        super(CategoryMeta, cls).__init__(name, parents, dct)

class Category(metaclass = CategoryMeta):
    def __str__(self):
        return self.__class__.__name__.lower()

    def is_of_category(self,cat):
        return isinstance(cat, self.__class__)

    __repr__ = __str__



class Expense(Category):
    pass

class Uncategorized(Expense):
    pass

class Income(Category):
    pass

_uncategorized = Uncategorized()


class Misc(Expense):
    pass

class Unexpected(Expense):
    pass

class Fixed(Expense):
    pass

class Food(Expense):
    pass

class Utilities(Expense):
    subtypes = [ "Internet", "Electricity", "Cellphone_Balance" ]

class Travel(Expense):
    subtypes = [ "Plane_Ticket", "Hotel_Reservation", "Train_Ticket" ]

class Leisure(Expense):
    pass

class Tax(Expense):
    subtypes = [ "TV" ]

class Shopping(Expense):
    subtypes = [ "Electronics", "Clothes", "Sports", "Home_Goods", "Furnishing", "Shopping_Misc", "Shoes", "Bag" ]

class Transport(Expense):
    subtypes = [ "Monthly_Ticket", "Single_Ticket", "Day_Ticket" ]

class Home(Expense):
    subtypes = [ "Rent", "Home_Repair", "Home_Service" ]

class Education(Expense):
    subtypes = [ "Course", "School_Book", "School_Suplies" ]

class German_Course(Course):
    pass

class Eating_Out(Food):
    subtypes = [ "Restaurant", "Fast_Food", "Icecream", "Drink", "Street_Food" ]

class Groceries(Food):
    subtypes = [ "Edeka", "Nahkauf", "Aldi" ]

class Body_And_Hygiene(Expense):
    subtypes = [ "Perfume", "Hair_Product", "Hairdresser", "Nails" ]
