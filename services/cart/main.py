from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import cart, health

app = FastAPI(title="Shopping Cart Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router, prefix="/v1")
app.include_router(cart.router, prefix="/v1")
