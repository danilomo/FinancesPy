class Category:

    def __init__(self, name, parent=None):
        self.name = name
        self._parent = parent

    def __str__(self):
        return self.name

    def matches(self, cat):

        if type(cat) is str and self.name == cat:
            return True

        if type(cat) is Category and self.name == cat.name:
            return True

        if self._parent is None:
            return False

        return self._parent.matches(cat)

    __repr__ = __str__


class Categories:

    def __init__(self, categories, default_category):
        self._categories = categories
        self._default = default_category

    def category(self, category):
        return self._categories.get(
            category,
            self._default
        )


def categories_from_list(cats):
    if not cats:
        return None

    def aux(catmap, cats, parent):
        for cat in cats:
            if type(cat) is str:
                category = Category(
                    cat,
                    parent
                )
                catmap[cat] = category
            elif type(cat) is dict:
                cat_name = cat.keys().__iter__().__next__()
                category = Category(
                    cat_name,
                    parent
                )
                catmap[cat_name] = category
                aux(catmap, cat[cat_name], category)

    catmap = {}
    aux(catmap, cats, None)
    return Categories(catmap, catmap["uncategorized"])
