from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import products, categories, health

app = FastAPI(
    title="Product Catalogue Service",
    description="SVC-1 — owns all product and category master data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(products.router, prefix="/v1")
app.include_router(categories.router, prefix="/v1")
