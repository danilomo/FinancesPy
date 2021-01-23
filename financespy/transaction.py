import financespy.money as money


class Transaction:
    def __init__(self, value, description, categories):
        self.value = money.Money(value)
        self.categories = categories
        self.description = description

    def as_expense(self):
        new_value = -1 * self.value.abs()
        return Transaction(new_value, self.description, self.categories)

    def as_income(self):
        return Transaction(self.value.abs(), self.description, self.categories)

    def __repr__(self):
        return ("%s, %s, %s" % (str(self.value),
                                self.description, str(self.categories)))

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

    def to_dict(self):
        result = {
            "value": int(self.value),
            "description": self.description,
            "categories": [cat.name for cat in self.categories]
        }

        if self.date is not None:
            result["date"] = {
                "day": self.date.day,
                "month": self.date.month,
                "year": self.date.year
            }

        return result


def parse_transaction(record, categories, separator=","):
    if isinstance(record, str):
        values = record.split(separator)
    elif isinstance(record, list):
        values = record
    else:
        raise Exception(str(type(record)) + " not allowed as parameter.")

    values = [s.strip() for s in values if s.strip()]

    if len(values) == 2:
        values.append(values[1])

    value = money.Money(values[0])
    description = values[1]

    category_list = list(set([categories.category(s) for s in values[2:]]))

    return Transaction(value, description, category_list)
