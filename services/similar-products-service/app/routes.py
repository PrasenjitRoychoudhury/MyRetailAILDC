from fastapi import APIRouter, HTTPException, Query
from app.db import DynamoDBClient
from app.models import SimilarProductsResponse, SimilarProduct, HealthResponse

router = APIRouter()
db_client = DynamoDBClient()


@router.get("/v1/health", response_model=HealthResponse)
async def health():
    return {
        "status": "ok",
        "service": "similar-products-service",
        "version": "1.0.0"
    }


@router.get("/v1/similar/{product_id}", response_model=SimilarProductsResponse)
async def get_similar_products(
    product_id: str,
    limit: int = Query(4, ge=1, le=20)
):
    """
    Get similar products from the same category.
    
    Args:
        product_id: The product ID to find similar products for
        limit: Maximum number of similar products to return (default: 4, max: 20)
    
    Returns:
        SimilarProductsResponse with list of similar products and count
    
    Raises:
        HTTPException: 404 if product not found
    """
    # Step 1: Get product and its category
    product = await db_client.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = product.get("category")
    if not category:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Step 2: Query similar products from same category
    similar_products = await db_client.query_similar_products(
        category=category,
        exclude_product_id=product_id,
        limit=limit
    )
    
    # Format response
    similar_product_list = [
        SimilarProduct(
            product_id=p["product_id"],
            name=p["name"],
            price=p["price"],
            image_url=p["image_url"],
            category=p["category"]
        )
        for p in similar_products
    ]
    
    return SimilarProductsResponse(
        similar_products=similar_product_list,
        count=len(similar_product_list)
    )
