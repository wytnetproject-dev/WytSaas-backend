from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.user import router as user_router, mock_router as mock_user_router
from routers.auth import router as auth_router
from routers.brand import router as brand_router
from routers.subscription import router as subscription_router
from routers.developer_bank_account import router as developer_bank_router


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


# Auto-create tables on startup
@app.on_event("startup")
async def startup_event():
    from db.db import engine, Base
    import models
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotently alter columns and add new sync columns
        try:
            await conn.execute(text("ALTER TABLE brands ALTER COLUMN current_stage TYPE VARCHAR(100);"))
        except Exception as e:
            print("Auto-alter current_stage column size failed:", e)
            
        try:
            await conn.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS external_user_id VARCHAR(255);"))
            await conn.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS sync_status VARCHAR(30) DEFAULT 'pending';"))
            await conn.execute(text("ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;"))
        except Exception as e:
            print("Auto-alter user_subscriptions columns skipped or failed:", e)


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include the user router
app.include_router(user_router)
app.include_router(mock_user_router)

# Include the brand router
app.include_router(brand_router)

# Include the subscription router
app.include_router(subscription_router)

# Include the developer bank account router
app.include_router(developer_bank_router)


