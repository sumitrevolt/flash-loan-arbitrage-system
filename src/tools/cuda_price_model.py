import torch
import numpy as np
from typing import List, Tuple

class CUDAPriceModel:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._build_model().to(self.device)
    
    def _build_model(self):
        return torch.nn.Sequential(
            torch.nn.Linear(10, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1)
        )
    
    def predict_price_movement(self, market_data: torch.Tensor) -> Tuple[float, float]:
        with torch.no_grad():
            market_data = market_data.to(self.device)
            prediction = self.model(market_data)
            confidence = self._calculate_confidence(prediction)
            return prediction.item(), confidence
    
    def _calculate_confidence(self, prediction: torch.Tensor) -> float:
        # Implement confidence calculation logic
        return 0.85  # Placeholder