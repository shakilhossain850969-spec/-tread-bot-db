import asyncio
from app.services.signal_engine import SignalEngine
from app.services.alert_system import AlertSystem

class MarketScanner:
    """
    Scans multiple assets and timeframes to find opportunities.
    """
    
    def __init__(self):
        self.engine = SignalEngine()
        self.default_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT"]
        self.default_timeframes = ["15m", "1H", "4H"]

    async def scan_market(self, pairs: list[str] = None, timeframes: list[str] = None) -> dict:
        """
        Runs the signal engine across all specified pairs and timeframes concurrently.
        """
        pairs = pairs or self.default_pairs
        timeframes = timeframes or self.default_timeframes
        
        tasks = []
        # Create a flat list of tasks
        for pair in pairs:
            for tf in timeframes:
                tasks.append(self.engine.generate_signal(pair, tf))
                
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_signals = []
        alerts_generated = []
        
        for res in results:
            if isinstance(res, Exception):
                print(f"Scan error: {res}")
                continue
                
            # Filter out HOLD signals to only show actionables
            if res.get("signal") in ["BUY", "SELL"] and res.get("confidence", 0) >= 60.0:
                valid_signals.append(res)
                
            # Process alerts
            alerts = AlertSystem.process_signal_for_alerts(res)
            alerts_generated.extend(alerts)
            
        # Sort by confidence descending
        valid_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return {
            "total_scanned": len(tasks),
            "actionable_signals": len(valid_signals),
            "signals": valid_signals,
            "alerts_triggered": alerts_generated
        }
