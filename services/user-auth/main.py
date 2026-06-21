from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, health
app = FastAPI(title="User & Auth Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
