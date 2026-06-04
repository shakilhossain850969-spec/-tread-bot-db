import pandas as pd
import math
from app.services.data_fetcher import DataFetcher
from app.services.indicators import IndicatorEngine
from app.services.candlestick_patterns import CandlestickPatterns
from app.services.price_action import PriceActionEngine
from app.services.ai_models.ensemble import XGBoostModel, LightGBMModel
from app.services.ai_models.lstm import LSTMModel

class SignalEngine:
    """
    Advanced Quantum Analyzer combining multiple dimensions of market data:
    Trend, Momentum, Price Action, Volume, Historical Fractals, and AI Models.
    """
    
    def __init__(self):
        self.xgb = XGBoostModel()
        self.lgb = LightGBMModel()
        self.lstm = LSTMModel()

    async def generate_signal(self, symbol: str, timeframe: str) -> dict:
        """End-to-end multi-dimensional signal generation pipeline."""
        df = await DataFetcher.get_ohlcv(symbol, timeframe)
        if df.empty or len(df) < 50:
            return self._empty_signal(symbol, timeframe)
            
        return await self._process_dataframe(df, symbol, timeframe)
        
    async def generate_signal_from_raw(self, symbol: str, timeframe: str, raw_candles: list) -> dict:
        """Process raw candles directly from Chrome Extension."""
        if not raw_candles or len(raw_candles) < 50:
            return self._empty_signal(symbol, timeframe)
            
        df = pd.DataFrame(raw_candles)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        # Ensure correct types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)
                
        return await self._process_dataframe(df, symbol, timeframe)

    async def _process_dataframe(self, df: pd.DataFrame, symbol: str, timeframe: str) -> dict:

        # 1. Compute Indicators & Patterns
        df = IndicatorEngine.add_all_indicators(df)
        df = CandlestickPatterns.add_patterns(df)
        
        # 2. Extract Analytics
        trend_res = self._analyze_trend(df)
        momentum_res = self._analyze_momentum(df)
        candlestick_res = CandlestickPatterns.get_latest_pattern_signal(df)
        sr_res = PriceActionEngine.calculate_support_resistance(df)
        volume_res = self._analyze_volume(df)
        fractal_res = PriceActionEngine.historical_fractal_match(df)
        
        # AI Models
        xgb_pred = self.xgb.predict(df)
        lgb_pred = self.lgb.predict(df)
        lstm_pred = self.lstm.predict(df)
        
        # 3. Aggregate 6-Layer Engine
        # Weights: Trend(20), Momentum(15), Price Action(25), Volume(10), Fractal(15), AI(15)
        
        pa_score = candlestick_res["score"] + sr_res["proximity_score"]
        ai_score = self._aggregate_ai(xgb_pred, lgb_pred, lstm_pred)
        
        total_score = (
            (trend_res["score"] * 0.20) +
            (momentum_res["score"] * 0.15) +
            (pa_score * 0.25) +
            (volume_res["score"] * 0.10) +
            (fractal_res["score"] * 0.15) +
            (ai_score * 0.15)
        )
        
        # Determine Final Signal (Threshold > 8.0 for BUY, < -8.0 for SELL out of theoretical max ~20-30 scaled)
        # To make it out of 100% confidence:
        confidence = min(abs(total_score) * 4.0, 100.0) # Scale up to 100
        
        if total_score >= 12.0:
            final_signal = "BUY"
        elif total_score <= -12.0:
            final_signal = "SELL"
        else:
            final_signal = "HOLD"

        # Construct reasoning list for transparency
        reasons = []
        if trend_res["reason"]: reasons.append(trend_res["reason"])
        if momentum_res["reason"]: reasons.append(momentum_res["reason"])
        reasons.extend(candlestick_res["reasons"])
        if sr_res["reason"]: reasons.append(sr_res["reason"])
        if volume_res["reason"]: reasons.append(volume_res["reason"])
        if fractal_res["reason"]: reasons.append(fractal_res["reason"])
        
        if not reasons and final_signal == "HOLD":
            reasons.append("Market is ranging/indecisive. Awaiting stronger setup.")

        # Calculate Risk Management
        last_close = df['close'].iloc[-1]
        atr = df['ATR'].iloc[-1] if 'ATR' in df.columns else (last_close * 0.02)
        
        if final_signal == "BUY":
            stop_loss = last_close - (atr * 1.5)
            take_profit = last_close + (atr * 3.0)
        elif final_signal == "SELL":
            stop_loss = last_close + (atr * 1.5)
            take_profit = last_close - (atr * 3.0)
        else:
            stop_loss = last_close
            take_profit = last_close

        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "signal": final_signal,
            "confidence": round(confidence, 2),
            "entry_price": round(last_close, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "reasons": reasons,
            "models": {
                "trend_score": round(trend_res["score"], 2),
                "momentum_score": round(momentum_res["score"], 2),
                "price_action_score": round(pa_score, 2),
                "fractal_score": round(fractal_res["score"], 2),
                "ai_score": round(ai_score, 2)
            }
        }

    def _analyze_trend(self, df: pd.DataFrame) -> dict:
        last = df.iloc[-1]
        score = 0.0
        reason = ""
        
        if 'EMA_50' in df.columns and 'EMA_200' in df.columns:
            if last['close'] > last['EMA_50'] > last['EMA_200']:
                score += 20.0
                reason = "Strong Uptrend (Price > EMA50 > EMA200)"
            elif last['close'] < last['EMA_50'] < last['EMA_200']:
                score -= 20.0
                reason = "Strong Downtrend (Price < EMA50 < EMA200)"
        
        if 'VWAP' in df.columns:
            if last['close'] > last['VWAP']:
                score += 10.0
            else:
                score -= 10.0
                
        return {"score": score, "reason": reason}

    def _analyze_momentum(self, df: pd.DataFrame) -> dict:
        last = df.iloc[-1]
        score = 0.0
        reason = ""
        
        if 'RSI' in df.columns:
            rsi = last['RSI']
            if rsi < 30:
                score += 30.0
                reason = "Oversold RSI (<30) - Momentum bottoming"
            elif rsi > 70:
                score -= 30.0
                reason = "Overbought RSI (>70) - Momentum peaking"
                
        if 'MACD' in df.columns:
            if IndicatorEngine.is_macd_bullish(df):
                score += 15.0
            elif IndicatorEngine.is_macd_bearish(df):
                score -= 15.0
                
        return {"score": score, "reason": reason}

    def _analyze_volume(self, df: pd.DataFrame) -> dict:
        score = 0.0
        reason = ""
        if IndicatorEngine.is_volume_increasing(df):
            # Volume is increasing. Check if it's bullish or bearish candle.
            last = df.iloc[-1]
            if last['close'] > last['open']:
                score += 25.0
                reason = "Rising volume on Bullish candle (Accumulation)"
            else:
                score -= 25.0
                reason = "Rising volume on Bearish candle (Distribution)"
        return {"score": score, "reason": reason}

    def _aggregate_ai(self, x_pred, l_pred, m_pred) -> float:
        def to_score(sig, conf):
            if sig == "BUY": return conf
            elif sig == "SELL": return -conf
            return 0.0
            
        x_score = to_score(x_pred['signal'], x_pred['confidence'])
        l_score = to_score(l_pred['signal'], l_pred['confidence'])
        m_score = to_score(m_pred['signal'], m_pred['confidence'])
        
        return (x_score * 0.4) + (l_score * 0.4) + (m_score * 0.2)

    def _empty_signal(self, symbol, tf):
        return {
            "symbol": symbol, "timeframe": tf, "signal": "HOLD",
            "confidence": 0.0, "entry_price": 0.0, "stop_loss": 0.0, "take_profit": 0.0,
            "reasons": ["Insufficient data"], "models": {}
        }
