from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import router

app = FastAPI(title="Product Catalogue Service", version="1.0.0")

app.include_router(router, prefix="/v1")

@app.get("/health")
async def health():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "product-catalogue"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
