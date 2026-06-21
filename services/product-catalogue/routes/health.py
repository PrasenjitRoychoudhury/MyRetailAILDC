from fastapi import APIRouter
from models import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", service="product-catalogue", version="1.0.0")
