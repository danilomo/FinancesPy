from datetime import date as Date
from typing import Union

from pydantic import BaseModel, Field


class TransactionModel(BaseModel):
    id: Union[int, str, None] = Field(default=None)
    value: Union[int, str]
    date: Union[Date, None] = Field(default=Date(1970, 1, 1))
    description: str = Field(default="")
    categories: list[str] = Field(default_factory=list)
