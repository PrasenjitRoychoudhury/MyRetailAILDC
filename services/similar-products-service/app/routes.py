from fastapi import APIRouter, HTTPException
from app.models import SimilarProductsResponse, SimilarProductItem
from app.db import get_product, query_similar_products

router = APIRouter(prefix="/v1", tags=["similar-products"])


@router.get("/similar/{product_id}")
async def get_similar_products(product_id: str) -> SimilarProductsResponse:
    """
    Retrieve up to 4 products from the same category as the given product.
    Always returns HTTP 200.
    """
    # Get the product to extract category
    product = await get_product(product_id)
    
    if not product:
        # Product not found, return empty list
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    category = product.get("category", "")
    
    if not category:
        # No category found, return empty list
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    # Query similar products from same category
    similar_items = await query_similar_products(category, product_id)
    
    # Convert to response models
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
