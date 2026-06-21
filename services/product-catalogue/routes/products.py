from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models import Product, ProductListResponse
import db

router = APIRouter(tags=["products"])

def _to_product(item: dict) -> Product:
    return Product(
        product_id=item["product_id"],
        name=item["name"],
        description=item["description"],
        price=float(item["price"]),
        category=item["category"],
        image_url=item["image_url"],
        rating_rate=float(item.get("rating_rate", 0)),
        rating_count=int(item.get("rating_count", 0)),
        stock_qty=int(item.get("stock_qty", 0)),
    )

@router.get("/products", response_model=ProductListResponse)
def list_products(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
):
    items, last_key = db.list_products(category=category, limit=limit, last_key=cursor)
    products = [_to_product(i) for i in items]
    return ProductListResponse(
        products=products,
        total=len(products),
        next_cursor=last_key.get("PK") if last_key else None,
    )

@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    item = db.get_product(product_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return _to_product(item)
