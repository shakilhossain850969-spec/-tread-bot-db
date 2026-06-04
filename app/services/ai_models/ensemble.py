import pandas as pd
import numpy as np
from .base import BaseModelWrapper

class XGBoostModel(BaseModelWrapper):
    """
    Wrapper for XGBoost classifier.
    Expects tabular data with indicators.
    """
    def _load_model(self):
        # In a real environment, we would do:
        # import xgboost as xgb
        # self.model = xgb.XGBClassifier()
        # self.model.load_model(self.model_path)
        pass

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Mock prediction based on indicator heuristics since we don't 
        have a physically trained model file in this environment.
        Simulates an XGBoost decision tree output.
        """
        if df.empty:
            return {"signal": "HOLD", "confidence": 0.0}
            
        last_row = df.iloc[-1]
        
        # Simulated XGBoost logic (usually complex non-linear splits)
        score = 50.0  # Base neutral
        
        # Momentum features
        if 'RSI' in last_row and not pd.isna(last_row['RSI']):
            if last_row['RSI'] < 30: score += 15
            elif last_row['RSI'] > 70: score -= 15
            
        if 'MACD_hist' in last_row and not pd.isna(last_row['MACD_hist']):
            if last_row['MACD_hist'] > 0: score += 10
            else: score -= 10
            
        # Trend features
        if 'close' in last_row and 'EMA_50' in last_row:
            if last_row['close'] > last_row['EMA_50']: score += 10
            else: score -= 10
            
        # Add some "model uncertainty/noise" to simulate probability
        noise = np.random.uniform(-5, 5)
        final_score = np.clip(score + noise, 0, 100)
        
        if final_score >= 65:
            return {"signal": "BUY", "confidence": final_score}
        elif final_score <= 35:
            # Invert score for sell confidence
            return {"signal": "SELL", "confidence": 100 - final_score}
        else:
            return {"signal": "HOLD", "confidence": 100 - abs(50 - final_score) * 2}


class LightGBMModel(BaseModelWrapper):
    """
    Wrapper for LightGBM classifier.
    """
    def _load_model(self):
        # import lightgbm as lgb
        pass

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Simulated LightGBM output. Very similar heuristic stub to XGBoost
        but with slight variations to simulate model ensemble diversity.
        """
        if df.empty:
            return {"signal": "HOLD", "confidence": 0.0}
            
        last_row = df.iloc[-1]
        score = 50.0
        
        # StochRSI is often favored by LightGBM in our simulated feature importance
        if 'StochRSI_k' in last_row and 'StochRSI_d' in last_row:
            if last_row['StochRSI_k'] > last_row['StochRSI_d'] and last_row['StochRSI_k'] < 0.2:
                score += 20
            elif last_row['StochRSI_k'] < last_row['StochRSI_d'] and last_row['StochRSI_k'] > 0.8:
                score -= 20
                
        # Bollinger Bands
        if 'close' in last_row and 'BB_low' in last_row and 'BB_high' in last_row:
            if last_row['close'] <= last_row['BB_low']: score += 15
            elif last_row['close'] >= last_row['BB_high']: score -= 15
            
        noise = np.random.uniform(-3, 3)
        final_score = np.clip(score + noise, 0, 100)
        
        if final_score >= 65:
            return {"signal": "BUY", "confidence": final_score}
        elif final_score <= 35:
            return {"signal": "SELL", "confidence": 100 - final_score}
        else:
            return {"signal": "HOLD", "confidence": 100 - abs(50 - final_score) * 2}
