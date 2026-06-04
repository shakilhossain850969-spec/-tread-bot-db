from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.routers import engine, quotex
from app.services.quotex_service import quotex_service

app = FastAPI(title="Lightweight Engine Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Start the Quotex connection in the background so we don't block the API
    asyncio.create_task(quotex_service.connect())

@app.on_event("shutdown")
async def shutdown_event():
    await quotex_service.disconnect()

# We include the engine router directly
# But wait, engine.py uses get_db and get_current_user dependencies.
# We need to mock those dependencies for the lightweight server to work without a DB!

# Mock the dependency overrides
from app.routers.engine import get_current_user, get_db, get_current_admin
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

async def mock_get_current_user():
    user = User()
    user.id = 1
    user.email = "test@example.com"
    user.is_approved = True
    return user

async def mock_get_db():
    yield None

app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_current_admin] = mock_get_current_user
app.dependency_overrides[get_db] = mock_get_db

app.include_router(engine.router)
app.include_router(quotex.router)

# Add basic mocks for auth and market so frontend doesn't crash
@app.post("/auth/login")
async def login():
    return {"access_token": "mock", "token_type": "bearer"}

@app.post("/auth/register")
async def register():
    return {"message": "ok"}

@app.get("/users/me")
async def users_me():
    return {
        "id": 1, "email": "test@example.com", "full_name": "Test User",
        "is_approved": True, "subscription_tier": "ELITE",
        "phone_number": "1234567890", "address": "123 Quantum Ave"
    }

@app.get("/market/live")
async def market_live():
    return {"data": []}

@app.get("/signals")
async def signals():
    return {"signals": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
