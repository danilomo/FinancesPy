
class Category:
    
    def __init__(self, name, parent = None):
        self._name = name
        self._parent = parent
        
    def __str__(self):
        return self._name

    def matches(self,cat):
        if self._name == cat:
            return True

        if self._parent is None:
            return False

        return self._parent.is_of_category(cat)
    
    __repr__ = __str__

class Categories:

    def __init__(self,categories, default_category):
        self._categories = categories
        self._default = default_category

    def category(self, category):
        return self._categories.get(
            category,
            self._default
        )

    
def categories_from_list(cats):
    
    def aux(catmap, cats, parent):
        for cat in cats:
            if type(cat) is str:
                category = Category(
                    cat,
                    parent
                )
                catmap[cat] = category
            elif type(cat) is tuple:
                category = Category(
                    cat[0],
                    parent
                )
                catmap[cat[0]] = category
                aux(catmap, cat[1], category)

    catmap = {}
    aux(catmap, cats, None)
    return Categories(catmap, catmap["uncategorized"])
                
    
default_categories = [
    "misc",
    "uncategorized",
    ("food", [ "groceries", "restaurant", "street_food"])
]


c = categories_from_list(default_categories)

print(c.category("restaurant").is_of_category("food"))
print(c.category("restaurant").is_of_category("misc"))
