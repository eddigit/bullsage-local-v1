"""
Technical Analysis Service - Centralized technical indicators calculation
"""
from typing import Dict, List, Any, Optional
import numpy as np
from core.config import logger


class TechnicalAnalysisService:
    """Service for calculating technical indicators"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi)
        except Exception as e:
            logger.warning(f"RSI calculation error: {e}")
            return 50.0
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """Calculate MACD indicator"""
        if len(prices) < slow + signal:
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "neutral"}
        
        try:
            prices_array = np.array(prices)
            
            # Calculate EMAs
            ema_fast = TechnicalAnalysisService._ema(prices_array, fast)
            ema_slow = TechnicalAnalysisService._ema(prices_array, slow)
            
            macd_line = ema_fast - ema_slow
            signal_line = TechnicalAnalysisService._ema(macd_line, signal)
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line[-1])
            current_signal = float(signal_line[-1])
            current_histogram = float(histogram[-1])
            
            # Determine trend
            if current_histogram > 0 and current_macd > current_signal:
                trend = "bullish"
            elif current_histogram < 0 and current_macd < current_signal:
                trend = "bearish"
            else:
                trend = "neutral"
            
            return {
                "macd": round(current_macd, 4),
                "signal": round(current_signal, 4),
                "histogram": round(current_histogram, 4),
                "trend": trend
            }
        except Exception as e:
            logger.warning(f"MACD calculation error: {e}")
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "neutral"}
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, Any]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0, "position": "middle", "bandwidth": 0}
        
        try:
            prices_array = np.array(prices[-period:])
            middle = float(np.mean(prices_array))
            std = float(np.std(prices_array))
            
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            current_price = prices[-1]
            
            # Determine position
            if current_price < lower:
                position = "oversold"
            elif current_price > upper:
                position = "overbought"
            elif current_price < middle:
                position = "lower_half"
            else:
                position = "upper_half"
            
            bandwidth = ((upper - lower) / middle) * 100 if middle > 0 else 0
            
            return {
                "upper": round(upper, 2),
                "middle": round(middle, 2),
                "lower": round(lower, 2),
                "position": position,
                "bandwidth": round(bandwidth, 2)
            }
        except Exception as e:
            logger.warning(f"Bollinger Bands calculation error: {e}")
            return {"upper": 0, "middle": 0, "lower": 0, "position": "middle", "bandwidth": 0}
    
    @staticmethod
    def calculate_moving_averages(prices: List[float]) -> Dict[str, Any]:
        """Calculate multiple moving averages and trend"""
        if len(prices) < 200:
            return {"ma20": 0, "ma50": 0, "ma200": 0, "trend": "neutral"}
        
        try:
            ma20 = float(np.mean(prices[-20:]))
            ma50 = float(np.mean(prices[-50:]))
            ma200 = float(np.mean(prices[-200:]))
            current = prices[-1]
            
            # Determine trend
            if ma20 > ma50 > ma200 and current > ma20:
                trend = "strong_bullish"
            elif ma20 > ma50 and current > ma50:
                trend = "bullish"
            elif ma20 < ma50 < ma200 and current < ma20:
                trend = "strong_bearish"
            elif ma20 < ma50 and current < ma50:
                trend = "bearish"
            else:
                trend = "neutral"
            
            return {
                "ma20": round(ma20, 2),
                "ma50": round(ma50, 2),
                "ma200": round(ma200, 2),
                "trend": trend
            }
        except Exception as e:
            logger.warning(f"MA calculation error: {e}")
            return {"ma20": 0, "ma50": 0, "ma200": 0, "trend": "neutral"}
    
    @staticmethod
    def calculate_support_resistance(prices: List[float]) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        if len(prices) < 20:
            return {"support": 0, "resistance": 0}
        
        try:
            recent = prices[-20:]
            support = float(min(recent))
            resistance = float(max(recent))
            return {"support": round(support, 2), "resistance": round(resistance, 2)}
        except Exception as e:
            logger.warning(f"Support/Resistance calculation error: {e}")
            return {"support": 0, "resistance": 0}
    
    @staticmethod
    def generate_trading_signal(prices: List[float], current_price: float) -> Dict[str, Any]:
        """Generate a complete trading signal based on all indicators"""
        
        # Calculate all indicators
        rsi = TechnicalAnalysisService.calculate_rsi(prices)
        macd = TechnicalAnalysisService.calculate_macd(prices)
        bb = TechnicalAnalysisService.calculate_bollinger_bands(prices)
        ma = TechnicalAnalysisService.calculate_moving_averages(prices) if len(prices) >= 200 else {"trend": "neutral"}
        sr = TechnicalAnalysisService.calculate_support_resistance(prices)
        
        # Calculate composite score
        score = 0
        reasons = []
        
        # RSI Analysis (weight: 3)
        if rsi < 25:
            score += 4
            reasons.append(f"🔥 RSI extrême ({rsi:.1f}) - Excellente opportunité d'achat")
        elif rsi < 30:
            score += 3
            reasons.append(f"RSI en survente ({rsi:.1f}) - Signal d'achat fort")
        elif rsi < 40:
            score += 2
            reasons.append(f"RSI favorable ({rsi:.1f})")
        elif rsi > 70:
            score -= 3
            reasons.append(f"RSI en surachat ({rsi:.1f}) - Éviter")
        
        # MACD Analysis
        if macd["trend"] == "bullish":
            score += 2
            reasons.append(f"MACD haussier avec histogramme positif ({macd['histogram']:+.4f})")
        elif macd["trend"] == "bearish":
            score -= 2
        
        # Bollinger Analysis
        if bb["position"] == "oversold":
            score += 3
            reasons.append("💰 Prix sur bande inférieure Bollinger")
        elif bb["position"] == "overbought":
            score -= 2
        
        # Trend Analysis
        trend = ma.get("trend", "neutral")
        if trend == "strong_bullish":
            score += 3
            reasons.append("🚀 Tendance fortement haussière")
        elif trend == "bullish":
            score += 2
            reasons.append("📈 Tendance haussière")
        elif trend == "strong_bearish":
            score -= 3
        elif trend == "bearish":
            score -= 2
        
        # Calculate levels
        support = sr.get("support", current_price * 0.95)
        resistance = sr.get("resistance", current_price * 1.10)
        
        stop_loss = max(support * 0.98, current_price * 0.92)
        take_profit_1 = current_price * 1.08
        take_profit_2 = min(resistance * 0.98, current_price * 1.15)
        
        # Determine action
        if score >= 5:
            action = "BUY"
            confidence = "high"
            message = "🟢 ACHAT recommandé - Signal fort"
        elif score >= 3:
            action = "BUY"
            confidence = "medium"
            message = "🟢 ACHAT suggéré - Signal modéré"
        elif score <= -4:
            action = "SELL"
            confidence = "high"
            message = "🔴 VENTE recommandée - Signal baissier fort"
        elif score <= -2:
            action = "SELL"
            confidence = "medium"
            message = "🔴 VENTE suggérée - Signal baissier"
        else:
            action = "WAIT"
            confidence = "low"
            message = "🟡 ATTENDRE - Pas de signal clair"
        
        return {
            "action": action,
            "confidence": confidence,
            "message": message,
            "score": round(score, 1),
            "reasons": reasons,
            "indicators": {
                "rsi": round(rsi, 1),
                "macd": macd,
                "bollinger": bb,
                "moving_averages": ma,
                "support_resistance": sr
            },
            "levels": {
                "entry": round(current_price, 2 if current_price >= 1 else 6),
                "stop_loss": round(stop_loss, 2 if stop_loss >= 1 else 6),
                "take_profit_1": round(take_profit_1, 2 if take_profit_1 >= 1 else 6),
                "take_profit_2": round(take_profit_2, 2 if take_profit_2 >= 1 else 6)
            }
        }


# Singleton instance
technical_analysis_service = TechnicalAnalysisService()
