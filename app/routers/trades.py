from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.trade import Trade, TradeResult
from app.models.signal import Signal
from app.models.user import User
from app.schemas.trade import TradeCreate, TradeClose, TradeResponse, TradeStats
from app.auth import get_current_user

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.user_id == current_user.id).order_by(Trade.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=TradeResponse, status_code=201)
async def create_trade(
    payload: TradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify signal exists
    result = await db.execute(select(Signal).where(Signal.id == payload.signal_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Signal not found")

    trade = Trade(
        user_id=current_user.id,
        signal_id=payload.signal_id,
        entry_price=payload.entry_price,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.patch("/{trade_id}/close", response_model=TradeResponse)
async def close_trade(
    trade_id: UUID,
    payload: TradeClose,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == current_user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    trade.exit_price = payload.exit_price
    trade.result = payload.result
    trade.closed_at = datetime.utcnow()
    if trade.entry_price:
        trade.pnl = round(((payload.exit_price - trade.entry_price) / trade.entry_price) * 100, 2)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.get("/stats", response_model=TradeStats)
async def trade_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Trade).where(Trade.user_id == current_user.id))
    trades = result.scalars().all()

    total = len(trades)
    wins = sum(1 for t in trades if t.result == TradeResult.win)
    losses = sum(1 for t in trades if t.result == TradeResult.loss)
    pending = sum(1 for t in trades if t.result == TradeResult.pending)
    accuracy = round((wins / (wins + losses)) * 100, 2) if (wins + losses) > 0 else 0
    total_pnl = round(sum(t.pnl or 0 for t in trades), 2)

    return TradeStats(
        total_trades=total, wins=wins, losses=losses, pending=pending,
        accuracy_rate=accuracy, total_pnl=total_pnl
    )
