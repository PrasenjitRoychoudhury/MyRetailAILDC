from pydantic import BaseModel, Field
from typing import List


class SimilarProductItem(BaseModel):
    product_id: str = Field(..., alias="id")
    name: str
    price: float
    image_url: str
    rating: float

    class Config:
        populate_by_name = True


class SimilarProductsResponse(BaseModel):
    product_id: str
    similar_products: List[SimilarProductItem]
    count: int
