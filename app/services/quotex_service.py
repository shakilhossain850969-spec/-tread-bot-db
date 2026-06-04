import asyncio
import time
import logging
from typing import Dict, Any, Optional

from api_quotex.client import AsyncQuotexClient, OrderDirection
from api_quotex.login import get_ssid

logger = logging.getLogger(__name__)

class QuotexService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuotexService, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.is_connected = False
            cls._instance.connection_task = None
            cls._instance.is_demo = True
            cls._instance.assets_cache = {}
        return cls._instance

    async def connect(self):
        """Initialize Playwright login and connect the WebSocket."""
        try:
            logger.info("Initializing Quotex Session (Playwright login)...")
            success, session_data = await get_ssid(is_demo=self.is_demo)
            
            if not success:
                logger.error("Failed to retrieve SSID for Quotex.")
                return False

            ssid_or_token = session_data.get("ssid") or session_data.get("token")
            if not ssid_or_token:
                logger.error("No valid SSID/token found in session data.")
                return False

            logger.info("SSID retrieved. Connecting AsyncQuotexClient...")
            self.client = AsyncQuotexClient(
                ssid=ssid_or_token,
                is_demo=self.is_demo,
                persistent_connection=True
            )
            
            connected = await self.client.connect()
            if connected:
                self.is_connected = True
                logger.info("Quotex WebSocket connected successfully!")
                
                # Start background task to keep data fresh
                if not self.connection_task or self.connection_task.done():
                    self.connection_task = asyncio.create_task(self._maintain_connection())
                    
                return True
            else:
                logger.error("Quotex WebSocket connection failed.")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Quotex: {e}")
            return False

    async def _maintain_connection(self):
        """Background loop to ensure client stays connected and fetches assets."""
        while True:
            try:
                if self.client and not self.client.is_connected:
                    logger.warning("Quotex disconnected. Reconnecting...")
                    await self.connect()
                
                if self.client and self.client.is_connected:
                    # Update assets cache periodically
                    assets = await self.client.get_available_assets()
                    if assets:
                        self.assets_cache = assets
                        
            except Exception as e:
                logger.error(f"Error in Quotex maintain loop: {e}")
                
            await asyncio.sleep(60)

    async def get_balance(self) -> float:
        if not self.client or not self.is_connected:
            return 0.0
        try:
            balance = await self.client.get_balance()
            return getattr(balance, "amount", getattr(balance, "balance", 0.0))
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0

    async def get_open_assets(self) -> Dict[str, Any]:
        """Returns open assets with >0 payout."""
        if not self.client or not self.is_connected:
            return {}
        
        try:
            assets = self.assets_cache or await self.client.get_available_assets()
            if not assets:
                return {}
            
            # Filter for open assets with payout > 0
            open_assets = {
                sym: info for sym, info in assets.items() 
                if info.get('is_open') and (info.get('payout') or 0) > 0
            }
            return open_assets
        except Exception as e:
            logger.error(f"Error fetching assets: {e}")
            return {}

    async def get_candles(self, symbol: str, timeframe: str = "1m", count: int = 100):
        """Fetch historical/live candles."""
        if not self.client or not self.is_connected:
            return []
            
        candles = []
        try:
            df = await self.client.get_candles_dataframe(symbol, timeframe, count=count)
            # Convert pandas DF to a list of dicts for JSON serialization
            for idx, row in df.iterrows():
                candles.append({
                    "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row.get('volume', 0.0))
                })
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            
        return candles

    async def place_order(self, symbol: str, amount: float, direction: str, duration: int = 60):
        """Place a trade."""
        if not self.client or not self.is_connected:
            return {"error": "Not connected to Quotex."}
        
        try:
            q_direction = OrderDirection.CALL if direction.upper() == "CALL" else OrderDirection.PUT
            order = await self.client.place_order(
                asset=symbol,
                amount=amount,
                direction=q_direction,
                duration=duration
            )
            return {
                "success": True,
                "order_id": order.order_id,
                "status": order.status.value if hasattr(order, 'status') else "Placed"
            }
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {"error": str(e)}

    async def disconnect(self):
        if self.connection_task:
            self.connection_task.cancel()
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            
quotex_service = QuotexService()
