from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes import router

app = FastAPI(
    title="Promotion Service",
    description="Manages promotional campaigns and discount codes",
    version="2.0.0"
)

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "promotion-service"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Validation Error",
            "status": 400,
            "detail": str(exc)
        }
    )
