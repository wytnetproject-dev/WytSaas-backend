from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.user import router as user_router
from routers.auth import router as auth_router
from routers.brand import router as brand_router
from routers.subscription import router as subscription_router


app = FastAPI(
    title="Wytnet API",
    description="A comprehensive backend API Built with FastAPI and SQLAlchemy",
    version="0.1.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for basic health check
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Wytnet API", "status": "operational"}

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include the user router
app.include_router(user_router)

# Include the brand router
app.include_router(brand_router)

# Include the subscription router
app.include_router(subscription_router)


