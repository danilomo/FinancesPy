class Category:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def __str__(self):
        return self.name

    def matches(self, cat):

        if type(cat) is str and self.name == cat:
            return True

        if type(cat) is Category and self.name == cat.name:
            return True

        if self.parent is None:
            return False

        return self.parent.matches(cat)

    __repr__ = __str__


class Categories:
    def __init__(self, categories, default_category):
        self._categories = categories
        self._default = default_category

    def category(self, category):
        return self._categories.get(category, self._default)

    @property
    def all(self):
        return list(self._categories.keys())

    def categories(self, expression):

        if expression[0] == "[":
            cats = expression[1:-1].split(",")
            return [self.category(cat) for cat in cats]

        if expression == "main_categories" or expression == "expenses":
            return self.children(self.category("expenses"))

        name, prop = expression.split(".")

        if prop == "children":
            return [
                cat
                for cat in self._categories.values()
                if cat.parent and cat.parent.name == name
            ]

        return []

    def children(self, category):
        name = category.name

        return [
            cat
            for cat in self._categories.values()
            if cat.parent and cat.parent.name == name
        ]


def categories_from_list(cats):
    if not cats:
        return None

    def aux(catmap, cats, parent):
        for cat in cats:
            if type(cat) is str:
                category = Category(cat, parent)
                catmap[cat] = category
            elif type(cat) is dict:
                cat_name = cat.keys().__iter__().__next__()
                category = Category(cat_name, parent)
                catmap[cat_name] = category
                aux(catmap, cat[cat_name], category)

    catmap = {}
    aux(catmap, cats, None)
    return Categories(catmap, catmap["uncategorized"])
