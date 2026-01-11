from __future__ import annotations

from typing import Any


class Category:
    def __init__(self, name: str, parent: Category | None = None) -> None:
        self.name = name
        self.parent = parent

    def __str__(self) -> str:
        return self.name

    def matches(self, cat: str | Category) -> bool:
        if type(cat) is str and self.name == cat:
            return True

        if type(cat) is Category and self.name == cat.name:
            return True

        if self.parent is None:
            return False

        return self.parent.matches(cat)

    __repr__ = __str__


class Categories:
    def __init__(
        self, categories: dict[str, Category], default_category: Category
    ) -> None:
        self._categories = categories
        self._default = default_category
        self._dict_representation: list[Any] | None = None

    def category(self, category: str, params: dict[str, str] | None = None) -> Category:
        if params is None:
            params = {}
        if category == "main_categories":
            category = "expenses"

        if category[0] == "$":
            category = params.get(category[1:], category)

        return self._categories.get(category, self._default)

    def to_dict(self) -> Any:
        return self._dict_representation

    @property
    def all(self) -> list[str]:
        return list(self._categories.keys())

    def categories(
        self, expression: str, params: dict[str, str] | None = None
    ) -> list[Category]:
        if params is None:
            params = {}
        if expression[0] == "[":
            cats = [cat.strip() for cat in expression[1:-1].split(",")]
            return [self.category(cat) for cat in cats]

        if expression in ["main_categories", "expenses"]:
            return self.children(self.category("expenses"))

        split = expression.split(".")

        if len(split) == 1:
            name = expression
            if name[0] == "$":
                name = params.get(name[1:], name)

            return [self.category(name)]

        name, prop = split

        if name[0] == "$":
            name = params.get(name[1:], name)

        if prop == "children":
            return [
                cat
                for cat in self._categories.values()
                if cat.parent and cat.parent.name == name
            ]

        return []

    def children(self, category: Category) -> list[Category]:
        name = category.name

        return [
            cat
            for cat in self._categories.values()
            if cat.parent and cat.parent.name == name
        ]


def categories_from_list(cats: list[Any] | None) -> Categories:
    if not cats:
        return Categories({}, Category("undefined"))

    def aux(
        catmap: dict[str, Category], cats: list[Any], parent: Category | None
    ) -> None:
        for cat in cats:
            if type(cat) is str:
                category = Category(cat, parent)
                catmap[cat] = category
            elif type(cat) is dict:
                cat_name = cat.keys().__iter__().__next__()
                category = Category(cat_name, parent)
                catmap[cat_name] = category
                aux(catmap, cat[cat_name], category)

    catmap: dict[str, Category] = {}
    aux(catmap, cats, None)
    categories = Categories(catmap, catmap["uncategorized"])
    categories._dict_representation = cats

    return categories
