from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.signal import Signal, SignalStatus
from app.models.user import User
from app.schemas.signal import SignalCreate, SignalUpdate, SignalResponse, SignalListResponse
from app.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("", response_model=SignalListResponse)
async def list_signals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Signal)
    if symbol:
        query = query.where(Signal.symbol == symbol.upper())
    if signal_type:
        query = query.where(Signal.signal_type == signal_type.upper())
    if status:
        query = query.where(Signal.status == status)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.order_by(Signal.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    signals = result.scalars().all()

    return SignalListResponse(signals=signals, total=total, page=page, page_size=page_size)


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.post("", response_model=SignalResponse, status_code=201)
async def create_signal(
    payload: SignalCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    rr = payload.compute_risk_reward()
    signal = Signal(
        symbol=payload.symbol.upper(),
        signal_type=payload.signal_type,
        confidence=payload.confidence,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        risk_reward=rr,
        timeframe=payload.timeframe,
        notes=payload.notes,
        created_by=admin.id,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


@router.patch("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: UUID,
    payload: SignalUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(signal, field, value)
    await db.commit()
    await db.refresh(signal)
    return signal


@router.delete("/{signal_id}", status_code=204)
async def delete_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    await db.delete(signal)
    await db.commit()
