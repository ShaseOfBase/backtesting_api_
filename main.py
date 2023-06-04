from fastapi import FastAPI
from typing import Optional
from dataclasses import dataclass

app = FastAPI()


@dataclass
class Item:
    name: str
    price: float
    is_offer: Optional[bool] = None

    def __repr__(self):
        return f"Item(name={self.name}, price={self.price}, is_offer={self.is_offer})"


import routes