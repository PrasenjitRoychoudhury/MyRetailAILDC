from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="promotion-service", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy", "service": "promotion-service"})
