import pandas as pd
import numpy as np

class PriceActionEngine:
    """
    Analyzes pure price action: Support/Resistance, and Historical Fractal Patterns.
    """
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window=20) -> dict:
        """
        Finds the nearest support and resistance levels.
        A simple approach: local mins and maxes over a rolling window.
        """
        if len(df) < window:
            return {"support": None, "resistance": None, "proximity_score": 0.0, "reason": ""}
            
        recent_highs = df['high'].rolling(window=window, center=False).max()
        recent_lows = df['low'].rolling(window=window, center=False).min()
        
        current_price = df['close'].iloc[-1]
        
        # We find the most prominent resistance above current price and support below
        res_levels = recent_highs.dropna().unique()
        res_levels = [r for r in res_levels if r > current_price]
        resistance = min(res_levels) if res_levels else None
        
        sup_levels = recent_lows.dropna().unique()
        sup_levels = [s for s in sup_levels if s < current_price]
        support = max(sup_levels) if sup_levels else None
        
        score = 0.0
        reason = ""
        
        if support and resistance:
            range_size = resistance - support
            # Distance from support and resistance
            dist_to_sup = current_price - support
            dist_to_res = resistance - current_price
            
            if dist_to_sup < (range_size * 0.15):
                score = 20.0
                reason = f"Bouncing off Support at {support:.2f}"
            elif dist_to_res < (range_size * 0.15):
                score = -20.0
                reason = f"Rejecting Resistance at {resistance:.2f}"
                
        return {
            "support": support,
            "resistance": resistance,
            "proximity_score": score,
            "reason": reason
        }

    @staticmethod
    def historical_fractal_match(df: pd.DataFrame, pattern_size=5) -> dict:
        """
        Looks at the last `pattern_size` candles and finds the most similar sequence 
        in the rest of the dataframe (at least 20 candles back) using Euclidean distance.
        Then checks what happened next in history to score it.
        """
        if len(df) < pattern_size * 3:
            return {"score": 0.0, "reason": "Not enough data for fractal match"}
            
        # Normalize the last N candles
        recent_closes = df['close'].iloc[-pattern_size:].values
        recent_norm = (recent_closes - recent_closes.min()) / (recent_closes.max() - recent_closes.min() + 1e-9)
        
        best_distance = float('inf')
        best_index = -1
        
        # Search through history (excluding the very recent data)
        search_space_end = len(df) - pattern_size - 1
        closes = df['close'].values
        
        for i in range(search_space_end - pattern_size):
            window = closes[i:i+pattern_size]
            window_norm = (window - window.min()) / (window.max() - window.min() + 1e-9)
            
            dist = np.linalg.norm(recent_norm - window_norm)
            if dist < best_distance:
                best_distance = dist
                best_index = i
                
        if best_index != -1 and best_distance < 1.0: # Threshold for similarity
            # Look at what happened *after* the matched pattern in history
            hist_match_end = best_index + pattern_size - 1
            if hist_match_end + 3 < len(df):
                future_price = closes[hist_match_end + 3]
                match_current_price = closes[hist_match_end]
                
                percent_change = (future_price - match_current_price) / match_current_price
                
                if percent_change > 0.002:
                    return {"score": 15.0, "reason": "Historical Fractal implies Upside"}
                elif percent_change < -0.002:
                    return {"score": -15.0, "reason": "Historical Fractal implies Downside"}
                    
        return {"score": 0.0, "reason": ""}
