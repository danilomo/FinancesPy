import financespy.money as money
from financespy.money import Money
from financespy.models import TransactionModel
from financespy.categories import Categories


class ParseTransactionError(Exception):
    def __init__(self, message):
        self.message = message


class Transaction:
    def __init__(self, value, description, categories, id=None, date=None):
        self.value = money.Money(value) if type(value) != Money else value
        self.categories = categories
        self.description = description
        self.id = id
        self.date = date

    def as_expense(self):
        new_value = -1 * self.value.abs()
        return Transaction(new_value, self.description, self.categories)

    def as_income(self):
        return Transaction(self.value.abs(), self.description, self.categories)

    def __repr__(self):
        return "%s, %s, %s" % (str(self.value), self.description, str(self.categories))

    def main_category(self):
        return self.categories[0]

    def add_category(self, category):
        self.categories.append(category)

    def matches_category(self, category):
        for c in self.categories:
            if c.matches(category):
                return True

        return False

    def __getattr__(self, name):
        if name.startswith("is_"):
            cat_name = name[3:]
            return self.matches_category(cat_name)

        raise AttributeError("Transaction object has no atrribute '%s'" % name)

    __str__ = __repr__

    def to_model_obj(self):
        return TransactionModel(
            id=self.id,
            value=int(self.value),
            date=self.date,
            categories=[str(cat) for cat in self.categories],
        )
    
    @staticmethod
    def to_transaction(model_obj: TransactionModel, cats: Categories):
        category_list = [cats.category(name) for name in  model_obj.categories]
        return Transaction(
            value = model_obj.value,
            categories=category_list,
            description=model_obj.description,  
            date=model_obj.date          
        )


def parse_transaction(record, categories, separator=","):
    if isinstance(record, str):
        values = record.split(separator)
    elif isinstance(record, list):
        values = record
    else:
        raise ParseTransactionError(
            f"{str(type(record))} type not allowed as parameter."
        )

    values = [s.strip() for s in values if s.strip()]

    if len(values) == 2:
        values.append(values[1])

    value = money.Money(values[0])
    description = values[1]

    category_list = list(set([categories.category(s) for s in values[2:]]))

    return Transaction(value, description, category_list)
