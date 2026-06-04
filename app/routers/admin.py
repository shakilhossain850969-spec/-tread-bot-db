from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User, UserRole
from app.models.signal import Signal, SignalStatus
from app.models.trade import Trade, TradeResult
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.notification import Notification
from app.schemas.user import UserResponse, UserAdminUpdate
from app.schemas.trade import AdminAnalytics, NotificationCreate, NotificationResponse
from app.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def send_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    notif = Notification(
        user_id=payload.user_id,
        title=payload.title,
        body=payload.body,
        type=payload.type,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


@router.get("/analytics", response_model=AdminAnalytics)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    total_signals = (await db.execute(select(func.count(Signal.id)))).scalar()
    active_signals = (await db.execute(
        select(func.count(Signal.id)).where(Signal.status == SignalStatus.active)
    )).scalar()
    total_trades = (await db.execute(select(func.count(Trade.id)))).scalar()
    wins = (await db.execute(select(func.count(Trade.id)).where(Trade.result == TradeResult.win))).scalar()
    losses = (await db.execute(select(func.count(Trade.id)).where(Trade.result == TradeResult.loss))).scalar()
    win_rate = round((wins / (wins + losses)) * 100, 2) if (wins + losses) > 0 else 0
    pro_subs = (await db.execute(
        select(func.count(Subscription.id)).where(Subscription.plan == SubscriptionPlan.pro)
    )).scalar()
    elite_subs = (await db.execute(
        select(func.count(Subscription.id)).where(Subscription.plan == SubscriptionPlan.elite)
    )).scalar()

    return AdminAnalytics(
        total_users=total_users, active_users=active_users,
        total_signals=total_signals, active_signals=active_signals,
        total_trades=total_trades, win_rate=win_rate,
        pro_subscribers=pro_subs, elite_subscribers=elite_subs,
    )
