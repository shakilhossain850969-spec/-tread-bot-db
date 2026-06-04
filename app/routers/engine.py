from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.engine import EnginePredictRequest, EnginePredictResponse, EngineScanRequest, EngineScanResponse
from app.services.signal_engine import SignalEngine
from app.services.scanner import MarketScanner
from app.models.notification import Notification

router = APIRouter(prefix="/engine", tags=["AI Engine"])

# Initialize singletons
engine = SignalEngine()
scanner = MarketScanner()

@router.post("/predict", response_model=EnginePredictResponse)
async def predict_asset(
    payload: EnginePredictRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run the AI Prediction Engine for a single asset and timeframe.
    """
    result = await engine.generate_signal(payload.symbol, payload.timeframe)
    return result

@router.post("/scan", response_model=EngineScanResponse)
async def run_market_scan(
    payload: EngineScanRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Run the Market Scanner across multiple pairs and timeframes. (Admin Only)
    Generates alerts if strong signals are detected.
    """
    result = await scanner.scan_market(payload.pairs, payload.timeframes)
    
    # Process alerts and save to DB
    for alert_data in result.get("alerts_triggered", []):
        notif = Notification(
            title=alert_data["title"],
            body=alert_data["body"],
            type=alert_data["type"]
        )
        db.add(notif)
    
    if result.get("alerts_triggered"):
        await db.commit()
        
    return result
