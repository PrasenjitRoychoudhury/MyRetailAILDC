from fastapi import APIRouter, HTTPException
from app.models import SimilarProductsResponse, SimilarProductItem
from app.db import get_product, query_similar_products

router = APIRouter(prefix="/v1", tags=["similar-products"])

@router.get("/similar/{product_id}", response_model=SimilarProductsResponse)
async def get_similar_products(product_id: str):
    """
    Retrieve up to 4 similar products from the same category.
    Always returns HTTP 200, with empty list if product not found or no similar products.
    """
    product = get_product(product_id)
    
    if not product:
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    category = product.get("category", "")
    
    if not category:
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    similar_items = query_similar_products(category, product_id)
    
    similar_products = [
        SimilarProductItem(
            product_id=item.get("product_id", ""),
            name=item.get("name", ""),
            price=float(item.get("price", 0)),
            image_url=item.get("image_url", ""),
            rating_rate=float(item.get("rating_rate", 0))
        )
        for item in similar_items
    ]
    
    return SimilarProductsResponse(
        product_id=product_id,
        similar_products=similar_products,
        count=len(similar_products)
    )
