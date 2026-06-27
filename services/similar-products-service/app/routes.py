from fastapi import APIRouter, HTTPException
from app.models import SimilarProductsResponse, SimilarProduct
from app.db import get_product_by_id, query_products_by_category

router = APIRouter(prefix="/v1", tags=["similar-products"])

@router.get("/similar/{product_id}", response_model=SimilarProductsResponse)
async def get_similar_products(product_id: str) -> SimilarProductsResponse:
    """
    Retrieve up to 4 similar products from the same category.
    Always returns HTTP 200 with empty list if product not found or no similar products exist.
    """
    product = get_product_by_id(product_id)
    
    if not product:
        return SimilarProductsResponse(product_id=product_id, similar_products=[], count=0)
    
    category = product.get("category", "")
    
    if not category:
        return SimilarProductsResponse(product_id=product_id, similar_products=[], count=0)
    
    similar = query_products_by_category(category, exclude_product_id=product_id)
    
    similar_list = []
    for item in similar[:4]:
        similar_list.append(
            SimilarProduct(
                product_id=item.get("id", ""),
                name=item.get("name", ""),
                price=float(item.get("price", 0)),
                image_url=item.get("image_url", ""),
                rating_rate=float(item.get("rating_rate", 0))
            )
        )
    
    return SimilarProductsResponse(
        product_id=product_id,
        similar_products=similar_list,
        count=len(similar_list)
    )
