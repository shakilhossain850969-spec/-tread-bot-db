from abc import ABC, abstractmethod
import pandas as pd

class BaseModelWrapper(ABC):
    """
    Abstract base class for all AI models in the prediction engine.
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self._load_model()

    @abstractmethod
    def _load_model(self):
        """Loads the pre-trained model weights from disk."""
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> dict:
        """
        Takes a dataframe with indicators and returns a prediction dictionary.
        Format:
        {
            "signal": "BUY" | "SELL" | "HOLD",
            "confidence": float (0.0 to 100.0)
        }
        """
        pass
