from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="coupon-service")

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "coupon-service"}
