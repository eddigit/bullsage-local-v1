"""
Service d'Analyse Multi-Timeframe pour BULL SAGE
Analyse la confluence des signaux sur plusieurs horizons temporels
Version robuste avec gestion d'erreurs
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class TimeframeSignal:
    """Signal pour un timeframe"""
    timeframe: str
    trend: str  # BULLISH, BEARISH, NEUTRAL
    strength: float  # 0-100
    signals: List[str]  # Liste des signaux détectés
    support: float
    resistance: float


class MultiTimeframeAnalyzer:
    """Analyseur multi-timeframe"""
    
    TIMEFRAMES = {
        "15m": 15,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
        "1w": 10080
    }
    
    SYMBOL_MAP = {
        "BTC": "XBTUSD",
        "ETH": "ETHUSD",
        "SOL": "SOLUSD",
        "XRP": "XRPUSD",
        "ADA": "ADAUSD",
        "DOT": "DOTUSD",
        "LINK": "LINKUSD"
    }
    
    def __init__(self):
        pass
    
    async def fetch_ohlc(self, symbol: str, interval_minutes: int) -> Optional[Dict]:
        """Récupère les données OHLC depuis Kraken"""
        
        pair = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}USD")
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval_minutes}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("error") and len(data["error"]) > 0:
                            return None
                        
                        result = data.get("result", {})
                        for key in result:
                            if key != "last":
                                return self._parse_ohlc(result[key])
        except Exception as e:
            logger.error(f"Erreur fetch OHLC {symbol}: {e}")
        
        return None
    
    def _parse_ohlc(self, data: List) -> Dict:
        """Parse les données OHLC"""
        return {
            "timestamps": [datetime.fromtimestamp(c[0]) for c in data],
            "opens": [float(c[1]) for c in data],
            "highs": [float(c[2]) for c in data],
            "lows": [float(c[3]) for c in data],
            "closes": [float(c[4]) for c in data],
            "volumes": [float(c[6]) for c in data]
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calcule EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcule RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: List[float]) -> Dict:
        """Calcule MACD simplifié"""
        if len(prices) < 26:
            return {"value": 0, "signal": 0, "histogram": 0}
        
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        macd_value = ema12 - ema26
        
        # Signal simplifié
        signal = macd_value * 0.9  # Approximation
        histogram = macd_value - signal
        
        return {"value": macd_value, "signal": signal, "histogram": histogram}
    
    def _calculate_bollinger(self, prices: List[float], period: int = 20) -> Dict:
        """Calcule Bollinger Bands"""
        if len(prices) < period:
            return {"upper": prices[-1] * 1.02, "middle": prices[-1], "lower": prices[-1] * 0.98}
        
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        
        return {
            "upper": sma + 2 * std,
            "middle": sma,
            "lower": sma - 2 * std
        }
    
    def analyze_timeframe(self, data: Dict, timeframe: str) -> TimeframeSignal:
        """Analyse un timeframe spécifique"""
        
        closes = data["closes"]
        highs = data["highs"]
        lows = data["lows"]
        
        if len(closes) < 50:
            return TimeframeSignal(
                timeframe=timeframe,
                trend="NEUTRAL",
                strength=50,
                signals=[],
                support=closes[-1] * 0.95,
                resistance=closes[-1] * 1.05
            )
        
        current_price = closes[-1]
        
        # Calculer les indicateurs
        rsi = self._calculate_rsi(closes)
        macd = self._calculate_macd(closes)
        bb = self._calculate_bollinger(closes)
        
        # EMAs
        ema20 = self._calculate_ema(closes, 20)
        ema50 = self._calculate_ema(closes, 50)
        ema200 = self._calculate_ema(closes, 200) if len(closes) >= 200 else ema50
        
        # Déterminer la tendance
        bullish_points = 0
        bearish_points = 0
        signals = []
        
        # EMA Trend
        if current_price > ema20 > ema50:
            bullish_points += 2
            signals.append("EMAs haussières")
        elif current_price < ema20 < ema50:
            bearish_points += 2
            signals.append("EMAs baissières")
        
        if len(closes) >= 200:
            if current_price > ema200:
                bullish_points += 1
                signals.append("Au-dessus EMA200")
            else:
                bearish_points += 1
                signals.append("En-dessous EMA200")
        
        # RSI
        if rsi < 30:
            bullish_points += 2
            signals.append("RSI survendu")
        elif rsi > 70:
            bearish_points += 2
            signals.append("RSI suracheté")
        elif rsi > 50:
            bullish_points += 1
        else:
            bearish_points += 1
        
        # MACD
        if macd["histogram"] > 0:
            bullish_points += 1
            signals.append("MACD haussier")
        else:
            bearish_points += 1
            signals.append("MACD baissier")
        
        # Bollinger
        if current_price < bb["lower"]:
            bullish_points += 1
            signals.append("Sous Bollinger inférieure")
        elif current_price > bb["upper"]:
            bearish_points += 1
            signals.append("Au-dessus Bollinger supérieure")
        
        # Calculer tendance et force
        total_points = bullish_points + bearish_points
        if bullish_points > bearish_points:
            trend = "BULLISH"
            strength = (bullish_points / max(total_points, 1)) * 100
        elif bearish_points > bullish_points:
            trend = "BEARISH"
            strength = (bearish_points / max(total_points, 1)) * 100
        else:
            trend = "NEUTRAL"
            strength = 50
        
        # Support/Résistance
        recent_lows = lows[-20:]
        recent_highs = highs[-20:]
        support = min(recent_lows)
        resistance = max(recent_highs)
        
        return TimeframeSignal(
            timeframe=timeframe,
            trend=trend,
            strength=round(strength, 2),
            signals=signals,
            support=round(support, 2),
            resistance=round(resistance, 2)
        )
    
    async def analyze(self, symbol: str, 
                      timeframes: List[str] = None) -> Dict:
        """Analyse multi-timeframe complète"""
        
        if timeframes is None:
            timeframes = ["1h", "4h", "1d"]
        
        logger.info(f"🔄 Analyse MTF {symbol} sur {timeframes}")
        
        # Récupérer les données pour chaque timeframe
        analyses = []
        current_price = None
        
        for tf in timeframes:
            interval = self.TIMEFRAMES.get(tf, 60)
            data = await self.fetch_ohlc(symbol, interval)
            
            if data and len(data["closes"]) > 0:
                if current_price is None:
                    current_price = data["closes"][-1]
                
                try:
                    tf_signal = self.analyze_timeframe(data, tf)
                    analyses.append(tf_signal)
                except Exception as e:
                    logger.error(f"Erreur analyse {tf}: {e}")
        
        if not analyses or current_price is None:
            return {"error": f"Impossible de récupérer les données pour {symbol}"}
        
        # Calculer confluence
        confluence_result = self._calculate_confluence(analyses)
        
        # Déterminer zones
        entry_stop_tp = self._calculate_levels(analyses, current_price)
        
        result = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "overall_bias": confluence_result["bias"],
            "confluence_score": confluence_result["score"],
            "recommendation": self._get_recommendation(confluence_result),
            "timeframes": [
                {
                    "timeframe": a.timeframe,
                    "trend": a.trend,
                    "strength": a.strength,
                    "signals": a.signals,
                    "support": a.support,
                    "resistance": a.resistance
                }
                for a in analyses
            ],
            **entry_stop_tp,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ MTF {symbol}: {confluence_result['bias']} (score: {confluence_result['score']})")
        
        return result
    
    def _calculate_confluence(self, analyses: List[TimeframeSignal]) -> Dict:
        """Calcule le score de confluence"""
        
        if not analyses:
            return {"bias": "NEUTRAL", "score": 50}
        
        # Pondération par timeframe (plus grand = plus important)
        weights = {
            "15m": 1,
            "1h": 2,
            "4h": 3,
            "1d": 4,
            "1w": 5
        }
        
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        for a in analyses:
            weight = weights.get(a.timeframe, 1)
            total_weight += weight
            
            if a.trend == "BULLISH":
                bullish_score += weight * (a.strength / 100)
            elif a.trend == "BEARISH":
                bearish_score += weight * (a.strength / 100)
        
        # Normaliser
        if total_weight > 0:
            bullish_norm = (bullish_score / total_weight) * 100
            bearish_norm = (bearish_score / total_weight) * 100
        else:
            bullish_norm = 50
            bearish_norm = 50
        
        # Déterminer biais
        diff = bullish_norm - bearish_norm
        
        if diff > 60:
            bias = "STRONG_BUY"
            score = min(95, 75 + diff / 4)
        elif diff > 30:
            bias = "BUY"
            score = 60 + diff / 3
        elif diff < -60:
            bias = "STRONG_SELL"
            score = max(5, 25 - abs(diff) / 4)
        elif diff < -30:
            bias = "SELL"
            score = 40 - abs(diff) / 3
        else:
            bias = "NEUTRAL"
            score = 50 + diff / 2
        
        return {"bias": bias, "score": round(score, 2)}
    
    def _calculate_levels(self, analyses: List[TimeframeSignal], 
                          current_price: float) -> Dict:
        """Calcule les niveaux d'entrée, SL et TP"""
        
        # Support/résistance moyens pondérés
        supports = []
        resistances = []
        
        for a in analyses:
            supports.append(a.support)
            resistances.append(a.resistance)
        
        avg_support = sum(supports) / len(supports) if supports else current_price * 0.95
        avg_resistance = sum(resistances) / len(resistances) if resistances else current_price * 1.05
        
        # Zone d'entrée
        entry_min = current_price * 0.995
        entry_max = current_price * 1.005
        
        # Stop loss sous support
        stop_loss = avg_support * 0.98
        
        # Take profits progressifs
        risk = current_price - stop_loss
        tp1 = current_price + risk * 1.5  # R:R 1:1.5
        tp2 = current_price + risk * 2.5  # R:R 1:2.5
        tp3 = avg_resistance  # Résistance
        
        return {
            "entry_zone": {
                "min": round(entry_min, 2),
                "max": round(entry_max, 2)
            },
            "stop_loss": round(stop_loss, 2),
            "take_profits": [
                {"level": 1, "price": round(tp1, 2), "pct_position": 30},
                {"level": 2, "price": round(tp2, 2), "pct_position": 40},
                {"level": 3, "price": round(tp3, 2), "pct_position": 30}
            ],
            "support": round(avg_support, 2),
            "resistance": round(avg_resistance, 2)
        }
    
    def _get_recommendation(self, confluence: Dict) -> str:
        """Génère une recommandation textuelle"""
        
        bias = confluence["bias"]
        score = confluence["score"]
        
        if bias == "STRONG_BUY":
            return f"🟢 ACHAT FORT - Confluence {score:.0f}% | Tendance haussière sur tous les timeframes."
        elif bias == "BUY":
            return f"🟢 ACHAT - Confluence {score:.0f}% | Tendance haussière majoritaire."
        elif bias == "STRONG_SELL":
            return f"🔴 VENTE FORTE - Confluence {score:.0f}% | Tendance baissière sur tous les timeframes."
        elif bias == "SELL":
            return f"🔴 VENTE - Confluence {score:.0f}% | Tendance baissière majoritaire."
        else:
            return f"🟡 NEUTRE - Confluence {score:.0f}% | Pas de consensus clair. Attendre."
    
    async def get_top_opportunities(self, symbols: List[str] = None) -> List[Dict]:
        """Trouve les meilleures opportunités"""
        
        if symbols is None:
            symbols = ["BTC", "ETH", "SOL", "XRP", "ADA"]
        
        opportunities = []
        
        for symbol in symbols:
            try:
                analysis = await self.analyze(symbol)
                if "error" not in analysis:
                    opportunities.append({
                        "symbol": symbol,
                        "bias": analysis["overall_bias"],
                        "score": analysis["confluence_score"],
                        "current_price": analysis["current_price"],
                        "recommendation": analysis["recommendation"]
                    })
            except Exception as e:
                logger.error(f"Erreur analyse {symbol}: {e}")
        
        # Trier par score de confluence
        opportunities.sort(key=lambda x: abs(x["score"] - 50), reverse=True)
        
        return opportunities


# Instance globale
mtf_analyzer = MultiTimeframeAnalyzer()
