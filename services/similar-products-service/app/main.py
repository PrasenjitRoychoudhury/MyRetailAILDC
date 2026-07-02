from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="similar-products-service", version="1.0.0")

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "similar-products-service"}
