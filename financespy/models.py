from typing import Optional
from pydantic import BaseModel, Field
from datetime import date as Date


class TransactionModel(BaseModel):    
    id: int | None = Field(default=None)
    value: int | str
    date:  Date | None = Field(default=Date(1970, 1, 1))
    description: str = Field(default="")
    categories: list[str] = Field(default_factory=list)
