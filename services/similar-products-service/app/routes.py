from fastapi import APIRouter, HTTPException
from app.models import SimilarProductsResponse, SimilarProduct
from app.db import get_product, scan_products_by_category

router = APIRouter(prefix="/v1", tags=["similar-products"])


@router.get("/similar/{product_id}")
async def get_similar_products(product_id: str) -> SimilarProductsResponse:
    """
    Retrieve up to 4 similar products from the same category.
    
    Returns HTTP 200 in all scenarios:
    - Products found and returned
    - Empty category with no similar products
    - Product ID does not exist
    """
    product = await get_product(product_id)
    
    if not product:
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    category = product.get("category")
    if not category:
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=[],
            count=0
        )
    
    products_in_category = await scan_products_by_category(category)
    
    similar_products_list = [
        SimilarProduct(
            product_id=p["product_id"],
            name=p["name"],
            price=p["price"],
            image_url=p["image_url"],
            rating=p["rating"]
        )
        for p in products_in_category
        if p["product_id"] != product_id
    ]
    
    similar_products_list.sort(key=lambda x: x.rating, reverse=True)
    
    similar_products_list = similar_products_list[:4]
    
    return SimilarProductsResponse(
        product_id=product_id,
        similar_products=similar_products_list,
        count=len(similar_products_list)
    )
