"""
Service d'indicateurs techniques avancés pour BULL SAGE
Inclut : RSI, MACD, Bollinger, Stochastique, ATR, Fibonacci
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    STRONG_BUY = 2
    BUY = 1
    NEUTRAL = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class TechnicalSignal:
    indicator: str
    signal: SignalStrength
    value: float
    description: str
    confidence: float


class TechnicalIndicators:
    """Calcul des indicateurs techniques avancés"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """RSI - Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float], 
                       fast: int = 12, 
                       slow: int = 26, 
                       signal: int = 9) -> Dict[str, float]:
        """MACD - Moving Average Convergence Divergence"""
        if len(prices) < slow + signal:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        prices_arr = np.array(prices)
        
        ema_fast = TechnicalIndicators._ema(prices_arr, fast)
        ema_slow = TechnicalIndicators._ema(prices_arr, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators._ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            "macd": round(float(macd_line[-1]), 4),
            "signal": round(float(signal_line[-1]), 4),
            "histogram": round(float(histogram[-1]), 4)
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], 
                                   period: int = 20, 
                                   std_dev: float = 2.0) -> Dict[str, float]:
        """Bandes de Bollinger"""
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0, "width": 0, "position": 50}
        
        prices_arr = np.array(prices[-period:])
        middle = np.mean(prices_arr)
        std = np.std(prices_arr)
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        width = (upper - lower) / middle * 100
        
        current_price = prices[-1]
        position = ((current_price - lower) / (upper - lower)) * 100 if upper != lower else 50
        
        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "width": round(width, 2),
            "position": round(position, 2)
        }
    
    @staticmethod
    def calculate_stochastic(highs: List[float], 
                              lows: List[float], 
                              closes: List[float],
                              k_period: int = 14,
                              d_period: int = 3) -> Dict[str, float]:
        """Stochastic Oscillator"""
        if len(closes) < k_period:
            return {"k": 50, "d": 50}
        
        lowest_low = min(lows[-k_period:])
        highest_high = max(highs[-k_period:])
        
        if highest_high == lowest_low:
            k = 50
        else:
            k = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100
        
        d = k
        
        return {"k": round(k, 2), "d": round(d, 2)}
    
    @staticmethod
    def calculate_atr(highs: List[float], 
                      lows: List[float], 
                      closes: List[float], 
                      period: int = 14) -> float:
        """ATR - Average True Range (volatilité)"""
        if len(closes) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        return round(np.mean(true_ranges[-period:]), 4)
    
    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
        """Niveaux de Fibonacci"""
        diff = high - low
        
        return {
            "0.0": round(low, 2),
            "0.236": round(low + diff * 0.236, 2),
            "0.382": round(low + diff * 0.382, 2),
            "0.5": round(low + diff * 0.5, 2),
            "0.618": round(low + diff * 0.618, 2),
            "0.786": round(low + diff * 0.786, 2),
            "1.0": round(high, 2)
        }
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return round(sum(prices[-period:]) / period, 2)
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        ema = TechnicalIndicators._ema(np.array(prices), period)
        return round(float(ema[-1]), 2)
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calcul EMA interne"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data, dtype=float)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema


class SignalGenerator:
    """Génère des signaux de trading basés sur les indicateurs"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze(self, 
                prices: List[float],
                highs: List[float] = None,
                lows: List[float] = None,
                volumes: List[float] = None) -> Dict:
        """Analyse complète avec tous les indicateurs"""
        
        if len(prices) < 50:
            return {"error": "Pas assez de données (minimum 50 bougies)"}
        
        highs = highs or prices
        lows = lows or prices
        volumes = volumes or [1] * len(prices)
        
        # Calcul de tous les indicateurs
        rsi = self.indicators.calculate_rsi(prices)
        macd = self.indicators.calculate_macd(prices)
        bollinger = self.indicators.calculate_bollinger_bands(prices)
        stochastic = self.indicators.calculate_stochastic(highs, lows, prices)
        atr = self.indicators.calculate_atr(highs, lows, prices)
        sma_20 = self.indicators.calculate_sma(prices, 20)
        sma_50 = self.indicators.calculate_sma(prices, 50)
        
        # Génération des signaux individuels
        signals = []
        
        # Signal RSI
        if rsi < 30:
            signals.append(TechnicalSignal("RSI", SignalStrength.BUY, rsi, "Survendu", 70))
        elif rsi < 20:
            signals.append(TechnicalSignal("RSI", SignalStrength.STRONG_BUY, rsi, "Très survendu", 85))
        elif rsi > 70:
            signals.append(TechnicalSignal("RSI", SignalStrength.SELL, rsi, "Suracheté", 70))
        elif rsi > 80:
            signals.append(TechnicalSignal("RSI", SignalStrength.STRONG_SELL, rsi, "Très suracheté", 85))
        else:
            signals.append(TechnicalSignal("RSI", SignalStrength.NEUTRAL, rsi, "Neutre", 50))
        
        # Signal MACD
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            strength = SignalStrength.STRONG_BUY if macd["histogram"] > abs(macd["macd"] * 0.1) else SignalStrength.BUY
            signals.append(TechnicalSignal("MACD", strength, macd["histogram"], "Croisement haussier", 75))
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            strength = SignalStrength.STRONG_SELL if abs(macd["histogram"]) > abs(macd["macd"] * 0.1) else SignalStrength.SELL
            signals.append(TechnicalSignal("MACD", strength, macd["histogram"], "Croisement baissier", 75))
        else:
            signals.append(TechnicalSignal("MACD", SignalStrength.NEUTRAL, macd["histogram"], "Neutre", 50))
        
        # Signal Bollinger
        if bollinger["position"] < 10:
            signals.append(TechnicalSignal("Bollinger", SignalStrength.STRONG_BUY, bollinger["position"], "Sous bande inférieure", 80))
        elif bollinger["position"] < 20:
            signals.append(TechnicalSignal("Bollinger", SignalStrength.BUY, bollinger["position"], "Proche bande inférieure", 65))
        elif bollinger["position"] > 90:
            signals.append(TechnicalSignal("Bollinger", SignalStrength.STRONG_SELL, bollinger["position"], "Au-dessus bande supérieure", 80))
        elif bollinger["position"] > 80:
            signals.append(TechnicalSignal("Bollinger", SignalStrength.SELL, bollinger["position"], "Proche bande supérieure", 65))
        else:
            signals.append(TechnicalSignal("Bollinger", SignalStrength.NEUTRAL, bollinger["position"], "Dans les bandes", 50))
        
        # Signal Stochastique
        if stochastic["k"] < 20:
            signals.append(TechnicalSignal("Stochastic", SignalStrength.BUY, stochastic["k"], "Survendu", 70))
        elif stochastic["k"] > 80:
            signals.append(TechnicalSignal("Stochastic", SignalStrength.SELL, stochastic["k"], "Suracheté", 70))
        else:
            signals.append(TechnicalSignal("Stochastic", SignalStrength.NEUTRAL, stochastic["k"], "Neutre", 50))
        
        # Signal Trend (SMA)
        current_price = prices[-1]
        if current_price > sma_20 > sma_50:
            signals.append(TechnicalSignal("Trend", SignalStrength.BUY, current_price, "Tendance haussière", 70))
        elif current_price < sma_20 < sma_50:
            signals.append(TechnicalSignal("Trend", SignalStrength.SELL, current_price, "Tendance baissière", 70))
        else:
            signals.append(TechnicalSignal("Trend", SignalStrength.NEUTRAL, current_price, "Tendance neutre", 50))
        
        # Score global
        total_score = sum(s.signal.value * (s.confidence / 100) for s in signals)
        max_score = len(signals) * 2
        
        global_score = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Recommandation finale
        if global_score > 50:
            recommendation = "STRONG_BUY"
            action = "🟢 Acheter maintenant"
        elif global_score > 20:
            recommendation = "BUY"
            action = "🟡 Envisager l'achat"
        elif global_score < -50:
            recommendation = "STRONG_SELL"
            action = "🔴 Vendre maintenant"
        elif global_score < -20:
            recommendation = "SELL"
            action = "🟠 Envisager la vente"
        else:
            recommendation = "HOLD"
            action = "⚪ Attendre"
        
        return {
            "current_price": current_price,
            "indicators": {
                "rsi": rsi,
                "macd": macd,
                "bollinger": bollinger,
                "stochastic": stochastic,
                "atr": atr,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "volatility_percent": round((atr / prices[-1]) * 100, 2) if prices[-1] > 0 else 0
            },
            "signals": [
                {
                    "indicator": s.indicator,
                    "signal": s.signal.name,
                    "value": s.value,
                    "description": s.description,
                    "confidence": s.confidence
                }
                for s in signals
            ],
            "summary": {
                "score": round(global_score, 2),
                "recommendation": recommendation,
                "action": action,
                "bullish_signals": sum(1 for s in signals if s.signal.value > 0),
                "bearish_signals": sum(1 for s in signals if s.signal.value < 0),
                "neutral_signals": sum(1 for s in signals if s.signal.value == 0)
            }
        }


class RiskManager:
    """Gestionnaire de risque"""
    
    @staticmethod
    def calculate_position_size(
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float
    ) -> Dict:
        """Calcule la taille de position optimale"""
        risk_amount = capital * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return {"error": "Stop loss identique au prix d'entrée"}
        
        position_size = risk_amount / price_risk
        position_value = position_size * entry_price
        
        return {
            "position_size": round(position_size, 6),
            "position_value": round(position_value, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_percent": risk_percent,
            "max_loss": round(risk_amount, 2)
        }
    
    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        atr: float,
        multiplier: float = 2.0,
        direction: str = "long"
    ) -> Dict:
        """Stop loss basé sur ATR"""
        stop_distance = atr * multiplier
        
        if direction == "long":
            stop_loss = entry_price - stop_distance
            take_profit_1 = entry_price + (stop_distance * 1.5)
            take_profit_2 = entry_price + (stop_distance * 2.5)
        else:
            stop_loss = entry_price + stop_distance
            take_profit_1 = entry_price - (stop_distance * 1.5)
            take_profit_2 = entry_price - (stop_distance * 2.5)
        
        return {
            "entry": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "stop_distance_percent": round((stop_distance / entry_price) * 100, 2),
            "take_profits": {
                "tp1": {"price": round(take_profit_1, 2), "rr_ratio": 1.5},
                "tp2": {"price": round(take_profit_2, 2), "rr_ratio": 2.5}
            }
        }
