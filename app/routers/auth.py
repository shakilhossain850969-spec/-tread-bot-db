import secrets
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.schemas.user import (
    UserCreate, LoginRequest, GoogleLoginRequest,
    TokenResponse, RefreshTokenRequest, ForgotPasswordRequest,
    ResetPasswordRequest, MessageResponse, UserResponse,
)
from app.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, verify_google_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token_response(user: User) -> TokenResponse:
    data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        address=payload.address,
        is_verified=False,
        is_approved=False,
    )
    db.add(user)
    await db.flush()

    # Create free subscription
    sub = Subscription(user_id=user.id, plan=SubscriptionPlan.free, status=SubscriptionStatus.active)
    db.add(sub)
    await db.commit()
    await db.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending admin approval")
    return _build_token_response(user)


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        google_data = await verify_google_token(payload.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = await db.execute(select(User).where(User.google_id == google_data["google_id"]))
    user = result.scalar_one_or_none()

    if not user:
        # Check by email
        result = await db.execute(select(User).where(User.email == google_data["email"]))
        user = result.scalar_one_or_none()
        if user:
            user.google_id = google_data["google_id"]
        else:
            user = User(
                email=google_data["email"],
                full_name=google_data["full_name"],
                avatar_url=google_data["avatar_url"],
                google_id=google_data["google_id"],
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            sub = Subscription(user_id=user.id, plan=SubscriptionPlan.free)
            db.add(sub)

    await db.commit()
    await db.refresh(user)
    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == UUID(decoded["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return _build_token_response(user)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        # TODO: send email with reset link
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.password_reset_token == payload.token)
    )
    user = result.scalar_one_or_none()
    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()
    return MessageResponse(message="Password reset successfully")
