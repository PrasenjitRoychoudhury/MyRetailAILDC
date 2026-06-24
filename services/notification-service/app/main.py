from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import router

app = FastAPI(title="notification-service", version="1.0.0")

app.include_router(router)

@app.get("/health")
async def health():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "notification-service"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
