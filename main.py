from fastapi import FastAPI
from routers.user import router as user_router
from routers.auth import router as auth_router

app = FastAPI(
    title="Wytnet API",
    description="A comprehensive backend API Built with FastAPI and SQLAlchemy",
    version="0.1.0"
)

# Root endpoint for basic health check
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Wytnet API", "status": "operational"}

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include the user router
app.include_router(user_router)

