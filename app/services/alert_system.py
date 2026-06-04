class AlertSystem:
    """
    Handles generation of alert events (Push Notifications, Webhooks).
    """
    
    @staticmethod
    def process_signal_for_alerts(signal_data: dict) -> list[dict]:
        """
        Analyzes a generated signal and returns a list of alert dictionaries if conditions are met.
        """
        alerts = []
        sig = signal_data.get("signal")
        conf = signal_data.get("confidence", 0)
        symbol = signal_data.get("symbol")
        tf = signal_data.get("timeframe")
        
        # 1. Strong Buy / Strong Sell
        if conf >= 80.0:
            if sig == "BUY":
                alerts.append({
                    "type": "alert",
                    "title": f"Strong BUY Alert: {symbol}",
                    "body": f"AI Engine detects a Strong BUY for {symbol} on {tf} timeframe with {conf}% confidence."
                })
            elif sig == "SELL":
                alerts.append({
                    "type": "alert",
                    "title": f"Strong SELL Alert: {symbol}",
                    "body": f"AI Engine detects a Strong SELL for {symbol} on {tf} timeframe with {conf}% confidence."
                })
                
        # Additional complex logic could be added here for Trend Reversal or Breakouts
        # by passing the dataframe down here, or reading flags attached to the signal_data.
        
        return alerts
