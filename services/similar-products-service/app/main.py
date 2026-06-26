from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import router

app = FastAPI(
    title="Similar Products Service",
    description="Microservice for retrieving similar products by category",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health")
async def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "similar-products-service"
        }
    )
