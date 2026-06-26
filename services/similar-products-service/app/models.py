from pydantic import BaseModel, Field
from typing import List


class SimilarProduct(BaseModel):
    product_id: str = Field(..., alias="product_id")
    name: str
    price: float
    image_url: str
    category: str

    class Config:
        populate_by_name = True


class SimilarProductsResponse(BaseModel):
    similar_products: List[SimilarProduct]
    count: int
