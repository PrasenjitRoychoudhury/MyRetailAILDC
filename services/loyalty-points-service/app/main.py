from fastapi import FastAPI
from datetime import datetime, timezone
from app.models import HealthResponse
from app import routes

app = FastAPI(title="Loyalty Points Service", version="1.0.0")

app.include_router(routes.router)

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for load balancer and monitoring."""
    return HealthResponse(
        status="healthy",
        service="loyalty-points",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
