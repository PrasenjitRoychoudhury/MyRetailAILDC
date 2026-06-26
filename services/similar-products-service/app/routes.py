from fastapi import APIRouter, Query, HTTPException
from app.models import SimilarProductsResponse, SimilarProduct
from app.db import get_product_category, get_similar_products

router = APIRouter(prefix="/v1", tags=["similar-products"])


@router.get("/similar/{product_id}", response_model=SimilarProductsResponse)
async def similar_products(
    product_id: str,
    limit: int = Query(4, ge=1, le=4)
):
    """
    Get similar products from the same category.
    Returns up to 4 products excluding the current product.
    """
    # Step 1: Get current product category
    category = await get_product_category(product_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Step 2: Find similar products
    similar = await get_similar_products(product_id, category, limit)
    
    return SimilarProductsResponse(
        similar_products=similar,
        count=len(similar)
    )


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "similar-products-service",
        "version": "1.0.0"
    }
