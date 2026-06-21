from fastapi import APIRouter
from models import Category, CategoryListResponse
import db

router = APIRouter(tags=["categories"])

@router.get("/categories", response_model=CategoryListResponse)
def list_categories():
    items = db.list_categories()
    categories = [
        Category(
            slug=i["slug"],
            display_name=i["display_name"],
            description=i["description"],
            product_count=int(i.get("product_count", 0)),
        )
        for i in items
    ]
    return CategoryListResponse(categories=categories)
