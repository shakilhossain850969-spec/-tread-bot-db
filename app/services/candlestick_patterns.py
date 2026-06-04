import pandas as pd
import numpy as np

class CandlestickPatterns:
    """
    Analyzes raw OHLCV data to detect candlestick patterns.
    """
    
    @staticmethod
    def add_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """Adds candlestick pattern columns to the dataframe."""
        if df.empty or len(df) < 3:
            return df
            
        df['body'] = df['close'] - df['open']
        df['body_abs'] = df['body'].abs()
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        df['range'] = df['high'] - df['low']
        
        # 1. Doji
        # Body is very small compared to the total range
        df['is_doji'] = (df['body_abs'] <= (df['range'] * 0.1)) & (df['range'] > 0)
        
        # 2. Hammer & Shooting Star
        # Hammer: Small body, long lower shadow (at least 2x body), very short upper shadow
        df['is_hammer'] = (df['lower_shadow'] >= (df['body_abs'] * 2)) & \
                          (df['upper_shadow'] <= (df['range'] * 0.1)) & \
                          (df['body_abs'] > 0)
                          
        # Shooting Star: Small body, long upper shadow (at least 2x body), very short lower shadow
        df['is_shooting_star'] = (df['upper_shadow'] >= (df['body_abs'] * 2)) & \
                                 (df['lower_shadow'] <= (df['range'] * 0.1)) & \
                                 (df['body_abs'] > 0)
        
        # 3. Engulfing
        # Shift data to get previous candle
        df['prev_open'] = df['open'].shift(1)
        df['prev_close'] = df['close'].shift(1)
        df['prev_body'] = df['body'].shift(1)
        
        # Bullish Engulfing: Prev is red, current is green and body entirely covers prev body
        df['bullish_engulfing'] = (df['prev_body'] < 0) & \
                                  (df['body'] > 0) & \
                                  (df['open'] <= df['prev_close']) & \
                                  (df['close'] > df['prev_open'])
                                  
        # Bearish Engulfing: Prev is green, current is red and body entirely covers prev body
        df['bearish_engulfing'] = (df['prev_body'] > 0) & \
                                  (df['body'] < 0) & \
                                  (df['open'] >= df['prev_close']) & \
                                  (df['close'] < df['prev_open'])
        
        return df

    @staticmethod
    def get_latest_pattern_signal(df: pd.DataFrame) -> dict:
        """Returns the signal score based on the latest 2 candles."""
        if 'bullish_engulfing' not in df.columns:
            df = CandlestickPatterns.add_patterns(df)
            
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0.0
        reason = []
        
        if last['bullish_engulfing']:
            score += 25.0
            reason.append("Bullish Engulfing Pattern")
        elif last['bearish_engulfing']:
            score -= 25.0
            reason.append("Bearish Engulfing Pattern")
            
        if last['is_hammer']:
            score += 15.0
            reason.append("Hammer (Bullish Rejection)")
        elif last['is_shooting_star']:
            score -= 15.0
            reason.append("Shooting Star (Bearish Rejection)")
            
        if last['is_doji']:
            # Indecision, look at previous candle trend
            if prev['body'] < 0:
                score += 5.0
                reason.append("Doji after downtrend (Possible reversal up)")
            else:
                score -= 5.0
                reason.append("Doji after uptrend (Possible reversal down)")
                
        return {
            "score": max(min(score, 30.0), -30.0), # Cap at +/- 30
            "reasons": reason
        }
