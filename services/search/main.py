from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import search, health
app = FastAPI(title="Search Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")
