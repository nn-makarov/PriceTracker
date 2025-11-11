from pydantic import BaseModel
from datetime import datetime
from typing import List

class ProductBase(BaseModel):
    title: str
    url: str
    current_price: float

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    product_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PriceHistoryBase(BaseModel):
    price: float

class PriceHistory(PriceHistoryBase):
    id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True