"""
🧠 BULL SAGE AI - Assistant de Trading Intelligent
Votre trader professionnel personnel

Ce module analyse en profondeur les marchés et génère des recommandations
claires et actionnables comme un vrai trader expert.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class TradeQuality(Enum):
    """Qualité d'une opportunité de trade"""
    A_PLUS = "A+"      # Setup parfait - 90%+ de confiance
    A = "A"            # Excellent setup - 80%+ de confiance
    B = "B"            # Bon setup - 70%+ de confiance
    C = "C"            # Setup moyen - éviter
    D = "D"            # Mauvais setup - ne pas trader


class MarketPhase(Enum):
    """Phase du marché"""
    ACCUMULATION = "Accumulation"      # Smart money achète
    MARKUP = "Markup"                  # Tendance haussière
    DISTRIBUTION = "Distribution"      # Smart money vend
    MARKDOWN = "Markdown"              # Tendance baissière
    RANGING = "Ranging"                # Consolidation


@dataclass
class TradeSetup:
    """Configuration complète d'un trade recommandé"""
    symbol: str
    quality: TradeQuality
    direction: str  # LONG ou SHORT
    confidence: float  # 0-100
    
    # Prix
    current_price: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # Risque
    risk_reward_ratio: float
    position_size_percent: float
    max_loss_percent: float
    potential_gain_percent: float
    
    # Analyse
    market_phase: MarketPhase
    trend_alignment: List[str]  # Timeframes alignés
    key_signals: List[str]
    warnings: List[str]
    
    # Timing
    urgency: str  # "IMMEDIATE", "WAIT_PULLBACK", "WAIT_CONFIRMATION"
    valid_until: str
    
    # Explication
    reasoning: str
    action_plan: str


class SmartMoneyAnalyzer:
    """Analyse du comportement du Smart Money"""
    
    def analyze_volume_profile(self, prices: List[float], volumes: List[float]) -> Dict:
        """Analyse le profil de volume pour détecter l'activité institutionnelle"""
        if len(prices) < 20 or len(volumes) < 20:
            return {"institutional_activity": "UNKNOWN", "bias": "NEUTRAL"}
        
        # Volume moyen
        avg_volume = sum(volumes[-20:]) / 20
        recent_volume = sum(volumes[-5:]) / 5
        
        # Variation de prix récente
        price_change = (prices[-1] - prices[-5]) / prices[-5] * 100
        
        # Détecter accumulation/distribution
        if recent_volume > avg_volume * 1.5:
            if price_change > 0:
                return {
                    "institutional_activity": "HIGH",
                    "bias": "ACCUMULATION",
                    "description": "Volume élevé avec prix en hausse = Institutions achètent"
                }
            elif price_change < 0:
                return {
                    "institutional_activity": "HIGH",
                    "bias": "DISTRIBUTION",
                    "description": "Volume élevé avec prix en baisse = Institutions vendent"
                }
        
        return {
            "institutional_activity": "NORMAL",
            "bias": "NEUTRAL",
            "description": "Activité institutionnelle normale"
        }


class TrendAnalyzer:
    """Analyse de tendance multi-timeframe"""
    
    KRAKEN_INTERVALS = {
        "5m": 5,
        "15m": 15,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }
    
    SYMBOL_MAP = {
        "BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD",
        "XRP": "XRPUSD", "ADA": "ADAUSD", "AVAX": "AVAXUSD",
        "DOT": "DOTUSD", "LINK": "LINKUSD", "MATIC": "MATICUSD",
        "DOGE": "DOGEUSD", "SHIB": "SHIBUSD", "LTC": "LTCUSD"
    }
    
    async def fetch_data(self, symbol: str, interval: int) -> Optional[Dict]:
        """Récupère les données OHLCV"""
        pair = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}USD")
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("result", {})
                        for key in result:
                            if key != "last":
                                ohlc = result[key]
                                return {
                                    "opens": [float(c[1]) for c in ohlc],
                                    "highs": [float(c[2]) for c in ohlc],
                                    "lows": [float(c[3]) for c in ohlc],
                                    "closes": [float(c[4]) for c in ohlc],
                                    "volumes": [float(c[6]) for c in ohlc]
                                }
        except Exception as e:
            logger.error(f"Erreur fetch {symbol}: {e}")
        return None
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def detect_trend(self, closes: List[float]) -> Tuple[str, float]:
        """Détecte la tendance et sa force"""
        if len(closes) < 50:
            return "NEUTRAL", 50
        
        ema8 = self.calculate_ema(closes, 8)
        ema21 = self.calculate_ema(closes, 21)
        ema50 = self.calculate_ema(closes, 50)
        price = closes[-1]
        
        # Score de tendance
        score = 0
        if price > ema8: score += 20
        if price > ema21: score += 20
        if price > ema50: score += 20
        if ema8 > ema21: score += 20
        if ema21 > ema50: score += 20
        
        if score >= 80:
            return "STRONG_UPTREND", score
        elif score >= 60:
            return "UPTREND", score
        elif score <= 20:
            return "STRONG_DOWNTREND", 100 - score
        elif score <= 40:
            return "DOWNTREND", 100 - score
        else:
            return "NEUTRAL", 50
    
    def detect_market_phase(self, closes: List[float], volumes: List[float]) -> MarketPhase:
        """Détecte la phase du marché (Wyckoff)"""
        if len(closes) < 50:
            return MarketPhase.RANGING
        
        # Tendance
        trend, _ = self.detect_trend(closes)
        
        # Volatilité
        recent_range = max(closes[-20:]) - min(closes[-20:])
        avg_price = sum(closes[-20:]) / 20
        volatility = recent_range / avg_price * 100
        
        # Volume trend
        vol_recent = sum(volumes[-10:]) / 10
        vol_old = sum(volumes[-30:-10]) / 20
        vol_increasing = vol_recent > vol_old * 1.2
        
        if trend in ["STRONG_UPTREND", "UPTREND"]:
            return MarketPhase.MARKUP
        elif trend in ["STRONG_DOWNTREND", "DOWNTREND"]:
            return MarketPhase.MARKDOWN
        elif volatility < 5 and vol_increasing:
            # Consolidation avec volume = accumulation ou distribution
            price_trend = closes[-1] > closes[-20]
            return MarketPhase.ACCUMULATION if price_trend else MarketPhase.DISTRIBUTION
        else:
            return MarketPhase.RANGING


class CandlestickAnalyzer:
    """Analyse des patterns de bougies pour timing d'entrée"""
    
    def analyze_candles(self, opens: List[float], highs: List[float], 
                        lows: List[float], closes: List[float]) -> Dict:
        """Analyse les dernières bougies pour détecter des patterns"""
        if len(closes) < 10:
            return {"pattern": None, "signal": "NEUTRAL", "strength": 0}
        
        patterns = []
        
        # Dernières bougies
        o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
        o2, h2, l2, c2 = opens[-2], highs[-2], lows[-2], closes[-2]
        o3, h3, l3, c3 = opens[-3], highs[-3], lows[-3], closes[-3]
        
        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        candle_range = h - l
        
        body2 = abs(c2 - o2)
        
        # === PATTERNS BULLISH ===
        
        # Hammer (marteau) - corps petit en haut, longue mèche basse
        if lower_wick > body * 2 and upper_wick < body * 0.5 and c > o:
            patterns.append({"name": "HAMMER", "signal": "BULLISH", "strength": 75})
        
        # Bullish Engulfing - bougie verte englobe la rouge précédente
        if c2 < o2 and c > o and c > o2 and o < c2:
            patterns.append({"name": "BULLISH_ENGULFING", "signal": "BULLISH", "strength": 80})
        
        # Morning Star (3 bougies)
        if c3 < o3 and body2 < body3 * 0.3 and c > o and c > (o3 + c3) / 2:
            patterns.append({"name": "MORNING_STAR", "signal": "BULLISH", "strength": 85})
        
        # Pin Bar Bullish - très longue mèche basse
        if lower_wick > candle_range * 0.66 and body < candle_range * 0.2:
            patterns.append({"name": "PIN_BAR_BULLISH", "signal": "BULLISH", "strength": 80})
        
        # === PATTERNS BEARISH ===
        
        # Shooting Star - corps petit en bas, longue mèche haute
        if upper_wick > body * 2 and lower_wick < body * 0.5 and c < o:
            patterns.append({"name": "SHOOTING_STAR", "signal": "BEARISH", "strength": 75})
        
        # Bearish Engulfing
        if c2 > o2 and c < o and c < o2 and o > c2:
            patterns.append({"name": "BEARISH_ENGULFING", "signal": "BEARISH", "strength": 80})
        
        # Evening Star (3 bougies)
        body3 = abs(c3 - o3)
        if c3 > o3 and body2 < body3 * 0.3 and c < o and c < (o3 + c3) / 2:
            patterns.append({"name": "EVENING_STAR", "signal": "BEARISH", "strength": 85})
        
        # Pin Bar Bearish
        if upper_wick > candle_range * 0.66 and body < candle_range * 0.2:
            patterns.append({"name": "PIN_BAR_BEARISH", "signal": "BEARISH", "strength": 80})
        
        # === PATTERNS NEUTRES ===
        
        # Doji - indécision
        if body < candle_range * 0.1:
            patterns.append({"name": "DOJI", "signal": "NEUTRAL", "strength": 50})
        
        # Résultat
        if not patterns:
            return {"pattern": None, "signal": "NEUTRAL", "strength": 0, "patterns": []}
        
        # Prendre le pattern le plus fort
        best = max(patterns, key=lambda x: x["strength"])
        return {
            "pattern": best["name"],
            "signal": best["signal"],
            "strength": best["strength"],
            "patterns": patterns
        }
    
    def find_entry_trigger(self, opens: List[float], highs: List[float],
                           lows: List[float], closes: List[float],
                           direction: str, current_price: float) -> Dict:
        """
        Trouve le prix d'entrée optimal basé sur les bougies
        Retourne un ordre LIMIT conditionnel
        """
        if len(closes) < 20:
            return {"type": "MARKET", "price": current_price}
        
        # Calculer les niveaux clés récents
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]
        
        # Support/Résistance court terme
        short_support = min(recent_lows)
        short_resistance = max(recent_highs)
        
        # Moyenne des clôtures récentes
        avg_close = sum(closes[-5:]) / 5
        
        if direction == "LONG":
            # Pour un LONG, on veut acheter sur un pullback vers le support
            # ou légèrement sous le prix actuel
            pullback_target = max(short_support, current_price * 0.995)
            
            # Niveau d'invalidation = sous le support
            invalidation = short_support * 0.98
            
            return {
                "type": "LIMIT",
                "price": round(pullback_target, 2),
                "trigger_condition": f"Entrer si le prix descend à ${pullback_target:,.2f}",
                "invalidation": round(invalidation, 2),
                "invalidation_msg": f"Annuler si le prix casse sous ${invalidation:,.2f}",
                "valid_for": "4 heures",
                "alternative": {
                    "type": "MARKET",
                    "condition": f"Ou entrer maintenant si la bougie 1H clôture au-dessus de ${avg_close:,.2f}"
                }
            }
        
        elif direction == "SHORT":
            # Pour un SHORT, on veut vendre sur un rebond vers la résistance
            pullback_target = min(short_resistance, current_price * 1.005)
            invalidation = short_resistance * 1.02
            
            return {
                "type": "LIMIT",
                "price": round(pullback_target, 2),
                "trigger_condition": f"Entrer si le prix monte à ${pullback_target:,.2f}",
                "invalidation": round(invalidation, 2),
                "invalidation_msg": f"Annuler si le prix casse au-dessus de ${invalidation:,.2f}",
                "valid_for": "4 heures",
                "alternative": {
                    "type": "MARKET",
                    "condition": f"Ou entrer maintenant si la bougie 1H clôture en-dessous de ${avg_close:,.2f}"
                }
            }
        
        return {"type": "WAIT", "reason": "Direction non déterminée"}


class ProTraderAI:
    """
    🧠 Intelligence de Trading Professionnelle
    
    Analyse comme un trader institutionnel et génère des recommandations
    claires et actionnables.
    """
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.smart_money = SmartMoneyAnalyzer()
        self.candle_analyzer = CandlestickAnalyzer()
        self.min_rr_ratio = 2.0  # Ratio risque/récompense minimum
        self.max_risk_per_trade = 2.0  # % max du portefeuille par trade
    
    def _determine_timeframe(self, aligned_timeframes: List[str], trends: Dict) -> Dict:
        """
        Détermine le timeframe principal du trade et la durée estimée
        basé sur les timeframes alignés et la force des tendances
        """
        # Calculer la force moyenne par timeframe
        tf_strength = {}
        for tf in ["1h", "4h", "1d"]:
            if tf in trends:
                tf_strength[tf] = trends[tf].get("strength", 50)
        
        # Déterminer le timeframe principal basé sur l'alignement
        if "1d" in aligned_timeframes and tf_strength.get("1d", 0) > 60:
            return {
                "timeframe": "1D",
                "trade_type": "SWING",
                "estimated_duration": "2 à 7 jours",
                "hold_time_min": "2 jours",
                "hold_time_max": "1 semaine",
                "description": "Trade de Swing - Position à tenir plusieurs jours"
            }
        elif "4h" in aligned_timeframes and tf_strength.get("4h", 0) > 55:
            return {
                "timeframe": "4H",
                "trade_type": "INTRADAY+",
                "estimated_duration": "4 à 24 heures",
                "hold_time_min": "4 heures",
                "hold_time_max": "24 heures",
                "description": "Trade Intraday étendu - Position sur quelques heures à 1 journée"
            }
        elif "1h" in aligned_timeframes:
            return {
                "timeframe": "1H",
                "trade_type": "INTRADAY",
                "estimated_duration": "1 à 4 heures",
                "hold_time_min": "1 heure",
                "hold_time_max": "4 heures",
                "description": "Trade Intraday - Position sur quelques heures"
            }
        else:
            # Par défaut, basé sur le timeframe le plus fort
            best_tf = max(tf_strength.keys(), key=lambda x: tf_strength.get(x, 0)) if tf_strength else "4h"
            if best_tf == "1d":
                return {
                    "timeframe": "1D",
                    "trade_type": "SWING",
                    "estimated_duration": "2 à 7 jours",
                    "hold_time_min": "2 jours",
                    "hold_time_max": "1 semaine",
                    "description": "Trade de Swing - Position à tenir plusieurs jours"
                }
            elif best_tf == "4h":
                return {
                    "timeframe": "4H",
                    "trade_type": "INTRADAY+",
                    "estimated_duration": "4 à 24 heures",
                    "hold_time_min": "4 heures",
                    "hold_time_max": "24 heures",
                    "description": "Trade Intraday étendu - Position sur quelques heures à 1 journée"
                }
            else:
                return {
                    "timeframe": "1H",
                    "trade_type": "INTRADAY",
                    "estimated_duration": "1 à 4 heures",
                    "hold_time_min": "1 heure",
                    "hold_time_max": "4 heures",
                    "description": "Trade Intraday - Position sur quelques heures"
                }
    
    async def analyze_asset(self, symbol: str) -> Dict:
        """Analyse complète d'un actif avec patterns de bougies"""
        
        # Récupérer données multi-timeframe
        data_1h = await self.trend_analyzer.fetch_data(symbol, 60)
        data_4h = await self.trend_analyzer.fetch_data(symbol, 240)
        data_1d = await self.trend_analyzer.fetch_data(symbol, 1440)
        
        if not all([data_1h, data_4h, data_1d]):
            return {"error": f"Données indisponibles pour {symbol}"}
        
        current_price = data_1h["closes"][-1]
        
        # Analyse de tendance par timeframe
        trend_1h, strength_1h = self.trend_analyzer.detect_trend(data_1h["closes"])
        trend_4h, strength_4h = self.trend_analyzer.detect_trend(data_4h["closes"])
        trend_1d, strength_1d = self.trend_analyzer.detect_trend(data_1d["closes"])
        
        # RSI multi-timeframe
        rsi_1h = self.trend_analyzer.calculate_rsi(data_1h["closes"])
        rsi_4h = self.trend_analyzer.calculate_rsi(data_4h["closes"])
        rsi_1d = self.trend_analyzer.calculate_rsi(data_1d["closes"])
        
        # Phase du marché
        market_phase = self.trend_analyzer.detect_market_phase(
            data_1d["closes"], data_1d["volumes"]
        )
        
        # Smart Money
        smart_money_analysis = self.smart_money.analyze_volume_profile(
            data_4h["closes"], data_4h["volumes"]
        )
        
        # Support / Résistance
        support, resistance = self._find_key_levels(data_1d)
        
        # 🕯️ ANALYSE DES BOUGIES (4H pour signal + 1D pour confirmation)
        candles_4h = self.candle_analyzer.analyze_candles(
            data_4h["opens"], data_4h["highs"], 
            data_4h["lows"], data_4h["closes"]
        )
        candles_1d = self.candle_analyzer.analyze_candles(
            data_1d["opens"], data_1d["highs"], 
            data_1d["lows"], data_1d["closes"]
        )
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "trends": {
                "1h": {"direction": trend_1h, "strength": strength_1h},
                "4h": {"direction": trend_4h, "strength": strength_4h},
                "1d": {"direction": trend_1d, "strength": strength_1d}
            },
            "rsi": {"1h": rsi_1h, "4h": rsi_4h, "1d": rsi_1d},
            "market_phase": market_phase.value,
            "smart_money": smart_money_analysis,
            "levels": {"support": support, "resistance": resistance},
            "candles": {
                "4h": candles_4h,
                "1d": candles_1d
            },
            # Garder les données pour entry trigger
            "_data_4h": data_4h,
            "_data_1d": data_1d
        }
    
    def _find_key_levels(self, data: Dict) -> Tuple[float, float]:
        """Trouve les niveaux clés de support et résistance"""
        highs = data["highs"][-50:]
        lows = data["lows"][-50:]
        
        # Support = plus bas récent significatif
        support = min(lows)
        
        # Résistance = plus haut récent significatif
        resistance = max(highs)
        
        return round(support, 2), round(resistance, 2)
    
    def _calculate_entry_stop_tp(self, current_price: float, direction: str,
                                   support: float, resistance: float) -> Dict:
        """Calcule les niveaux d'entrée, stop et take profits"""
        
        if direction == "LONG":
            # Entry légèrement sous le prix actuel (pullback)
            entry = current_price * 0.998
            
            # Stop sous le support
            stop = support * 0.98
            
            # Take profits progressifs
            risk = entry - stop
            tp1 = entry + risk * 1.5  # R:R 1:1.5
            tp2 = entry + risk * 2.5  # R:R 1:2.5
            tp3 = min(resistance, entry + risk * 4)  # R:R 1:4 ou résistance
            
        else:  # SHORT
            entry = current_price * 1.002
            stop = resistance * 1.02
            risk = stop - entry
            tp1 = entry - risk * 1.5
            tp2 = entry - risk * 2.5
            tp3 = max(support, entry - risk * 4)
        
        rr_ratio = abs(tp2 - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0
        
        return {
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "tp3": round(tp3, 2),
            "rr_ratio": round(rr_ratio, 2),
            "risk_percent": round(abs(entry - stop) / entry * 100, 2),
            "potential_gain": round(abs(tp2 - entry) / entry * 100, 2)
        }
    
    def _determine_trade_quality(self, analysis: Dict) -> Tuple[TradeQuality, float, List[str], List[str]]:
        """Détermine la qualité du trade et les signaux"""
        
        signals = []
        warnings = []
        score = 50  # Base
        
        trends = analysis["trends"]
        rsi = analysis["rsi"]
        phase = analysis["market_phase"]
        smart_money = analysis["smart_money"]
        
        # === ALIGNEMENT DES TENDANCES ===
        bullish_count = sum(1 for t in trends.values() if "UPTREND" in t["direction"])
        bearish_count = sum(1 for t in trends.values() if "DOWNTREND" in t["direction"])
        
        if bullish_count == 3:
            score += 25
            signals.append("✅ Toutes les tendances alignées HAUSSIÈRES")
        elif bearish_count == 3:
            score += 25
            signals.append("✅ Toutes les tendances alignées BAISSIÈRES")
        elif bullish_count >= 2:
            score += 15
            signals.append("📈 Majorité des tendances haussières")
        elif bearish_count >= 2:
            score += 15
            signals.append("📉 Majorité des tendances baissières")
        else:
            score -= 10
            warnings.append("⚠️ Tendances non alignées - prudence")
        
        # === RSI ===
        avg_rsi = (rsi["1h"] + rsi["4h"] + rsi["1d"]) / 3
        
        if avg_rsi < 30:
            score += 15
            signals.append("🔥 RSI survendu - opportunité d'achat")
        elif avg_rsi > 70:
            score += 15
            signals.append("🔥 RSI suracheté - opportunité de vente")
        elif 40 < avg_rsi < 60:
            signals.append("📊 RSI neutre")
        
        # Divergence RSI (simplifié)
        if rsi["1h"] < 40 and rsi["4h"] > 50:
            warnings.append("⚠️ Possible divergence RSI - confirmer")
        
        # === PHASE DU MARCHÉ ===
        if phase == "Accumulation":
            score += 15
            signals.append("💰 Phase d'accumulation - Smart Money achète")
        elif phase == "Markup":
            score += 10
            signals.append("🚀 Phase de hausse en cours")
        elif phase == "Distribution":
            score -= 10
            warnings.append("⚠️ Phase de distribution - Smart Money vend")
        elif phase == "Markdown":
            score -= 5
            signals.append("📉 Phase de baisse - chercher shorts")
        
        # === SMART MONEY ===
        if smart_money["institutional_activity"] == "HIGH":
            if smart_money["bias"] == "ACCUMULATION":
                score += 15
                signals.append("🐋 Activité institutionnelle forte - ACHAT")
            elif smart_money["bias"] == "DISTRIBUTION":
                score += 15
                signals.append("🐋 Activité institutionnelle forte - VENTE")
        
        # === QUALITÉ FINALE ===
        confidence = min(95, max(10, score))
        
        if score >= 85:
            quality = TradeQuality.A_PLUS
        elif score >= 70:
            quality = TradeQuality.A
        elif score >= 55:
            quality = TradeQuality.B
        elif score >= 40:
            quality = TradeQuality.C
        else:
            quality = TradeQuality.D
        
        return quality, confidence, signals, warnings
    
    async def get_trade_recommendation(self, symbol: str) -> Dict:
        """
        🎯 Génère une recommandation de trade complète
        Comme un trader pro vous conseillerait
        
        RÈGLES ÉQUILIBRÉES (ajustées pour générer plus de signaux):
        - Recommande un trade si les tendances principales sont alignées
        - WAIT si vraiment aucune direction claire
        - SHORT = autorisé si conditions baissières confirmées
        - Minimum qualité B pour trader (plus accessible)
        """
        
        analysis = await self.analyze_asset(symbol)
        
        if "error" in analysis:
            return analysis
        
        # Déterminer direction avec RÈGLES ÉQUILIBRÉES
        trends = analysis["trends"]
        rsi = analysis["rsi"]
        
        # Compter les tendances
        bullish = sum(1 for t in trends.values() if "UPTREND" in t["direction"])
        bearish = sum(1 for t in trends.values() if "DOWNTREND" in t["direction"])
        
        # Force des tendances
        strength_1d = trends.get("1d", {}).get("strength", 50)
        strength_4h = trends.get("4h", {}).get("strength", 50)
        trend_1d = trends.get("1d", {}).get("direction", "NEUTRAL")
        trend_4h = trends.get("4h", {}).get("direction", "NEUTRAL")
        
        # Calculer le momentum récent
        momentum_bullish = rsi["1h"] > rsi["4h"] and rsi["4h"] > 45
        momentum_bearish = rsi["1h"] < rsi["4h"] and rsi["4h"] < 55
        
        # === RÈGLES ÉQUILIBRÉES POUR DIRECTION ===
        direction = "WAIT"  # Par défaut = pas de trade
        
        # LONG: si tendance majoritairement haussière ET RSI pas en surachat extrême
        if bullish >= 2 and (strength_1d >= 50 or strength_4h >= 50):
            # Vérifier que RSI n'est pas en surachat extrême
            if rsi["1d"] < 75 and rsi["4h"] < 75:
                direction = "LONG"
            else:
                direction = "WAIT"  # RSI trop haut
        
        # SHORT: si tendance majoritairement baissière
        elif bearish >= 2 and (strength_1d >= 50 or strength_4h >= 50):
            # Vérifier que RSI n'est pas en survente extrême
            if rsi["1d"] > 25 and rsi["4h"] > 25:
                direction = "SHORT"
            else:
                direction = "WAIT"  # RSI trop bas
        
        # Qualité du trade
        quality, confidence, signals, warnings = self._determine_trade_quality(analysis)
        
        # === FORCER WAIT SI QUALITÉ INSUFFISANTE (qualité C ou D) ===
        if quality in [TradeQuality.C, TradeQuality.D]:
            direction = "WAIT"
            warnings.insert(0, "⚠️ QUALITÉ FAIBLE - Attendre un meilleur setup")
        
        # Niveaux
        levels = self._calculate_entry_stop_tp(
            analysis["current_price"],
            direction if direction != "WAIT" else "LONG",  # Calculs par défaut
            analysis["levels"]["support"],
            analysis["levels"]["resistance"]
        )
        
        # 🕯️ ANALYSE DES BOUGIES - Déterminer condition d'entrée
        candle_info = analysis.get("candles", {}).get("4h", {})
        candle_patterns = candle_info.get("patterns", [])
        candle_signal = candle_info.get("signal", "NEUTRAL")
        
        # Trouver condition d'entrée avec ordre LIMIT
        entry_trigger = None
        if direction != "WAIT" and "_data_4h" in analysis:
            data_4h = analysis["_data_4h"]
            entry_trigger = self.candle_analyzer.find_entry_trigger(
                data_4h["opens"], data_4h["highs"], 
                data_4h["lows"], data_4h["closes"],
                direction
            )
        elif direction == "WAIT":
            # Même si WAIT, donner les conditions pour entrer plus tard
            if "_data_4h" in analysis:
                data_4h = analysis["_data_4h"]
                # Chercher un trigger LONG potentiel (plus prudent)
                entry_trigger = self.candle_analyzer.find_entry_trigger(
                    data_4h["opens"], data_4h["highs"], 
                    data_4h["lows"], data_4h["closes"],
                    "LONG"  # Chercher condition LONG par défaut
                )
        
        # Urgence
        if quality in [TradeQuality.A_PLUS, TradeQuality.A] and direction != "WAIT":
            if analysis["rsi"]["1h"] < 35 or analysis["rsi"]["1h"] > 65:
                urgency = "IMMEDIATE"
            else:
                urgency = "WAIT_PULLBACK"
        else:
            urgency = "NO_TRADE"
        
        # Timeframes alignés
        aligned = [tf for tf, data in trends.items() 
                   if (direction == "LONG" and "UPTREND" in data["direction"]) or
                      (direction == "SHORT" and "DOWNTREND" in data["direction"])]
        
        # Déterminer le timeframe principal et la durée estimée
        timeframe_info = self._determine_timeframe(aligned, analysis["trends"])
        
        # Raisonnement (avec info bougies)
        reasoning = self._generate_reasoning(analysis, direction, quality, signals, candle_patterns)
        
        # Plan d'action (avec condition d'entrée)
        action_plan = self._generate_action_plan(direction, quality, levels, urgency, entry_trigger)
        
        # Ajouter avertissement si SHORT recommandé
        if direction == "SHORT":
            warnings.append("⚠️ SHORT = Plus risqué que LONG en crypto")
            warnings.append("⚠️ Utilisez un stop loss serré")
        
        # Ajouter info patterns de bougies aux signaux
        for pattern in candle_patterns[:2]:  # Max 2 patterns
            signals.append(f"🕯️ Pattern: {pattern}")
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            
            "recommendation": {
                "quality": quality.value,
                "direction": direction,
                "confidence": confidence,
                "urgency": urgency,
                "timeframe": timeframe_info["timeframe"],
                "trade_type": timeframe_info["trade_type"],
                "estimated_duration": timeframe_info["estimated_duration"],
                "hold_time_min": timeframe_info["hold_time_min"],
                "hold_time_max": timeframe_info["hold_time_max"]
            },
            
            "levels": levels,
            
            # 🎯 CONDITIONS D'ENTRÉE
            "entry_trigger": entry_trigger,
            
            # 🕯️ ANALYSE BOUGIES
            "candle_analysis": {
                "patterns": candle_patterns,
                "signal": candle_signal
            },
            
            "analysis": {
                "market_phase": analysis["market_phase"],
                "trend_alignment": aligned,
                "rsi": analysis["rsi"],
                "smart_money": analysis["smart_money"]["bias"]
            },
            
            "signals": signals,
            "warnings": warnings,
            
            "reasoning": reasoning,
            "action_plan": action_plan,
            
            "position_sizing": {
                "recommended_risk": f"{min(self.max_risk_per_trade, 2 if quality.value in ['A+', 'A'] else 1)}%",
                "max_position": f"{5 if quality.value in ['A+', 'A'] else 3}% du portefeuille"
            }
        }
    
    def _generate_reasoning(self, analysis: Dict, direction: str, 
                            quality: TradeQuality, signals: List[str],
                            candle_patterns: List[str] = None) -> str:
        """Génère l'explication du raisonnement avec patterns de bougies"""
        
        phase = analysis["market_phase"]
        price = analysis["current_price"]
        
        # Info bougies
        candle_section = ""
        if candle_patterns:
            candle_section = f"""
**🕯️ Patterns de Bougies (4H)**:
{chr(10).join('• ' + p for p in candle_patterns[:3])}
"""
        
        reasoning = f"""
📊 **ANALYSE {analysis['symbol']}** @ ${price:,.2f}

**Phase du marché**: {phase}

**Tendances**:
• 1H: {analysis['trends']['1h']['direction']} ({analysis['trends']['1h']['strength']:.0f}%)
• 4H: {analysis['trends']['4h']['direction']} ({analysis['trends']['4h']['strength']:.0f}%)
• 1D: {analysis['trends']['1d']['direction']} ({analysis['trends']['1d']['strength']:.0f}%)

**RSI**:
• 1H: {analysis['rsi']['1h']:.1f}
• 4H: {analysis['rsi']['4h']:.1f}
• 1D: {analysis['rsi']['1d']:.1f}
{candle_section}
**Signaux clés**:
{chr(10).join('• ' + s for s in signals)}

**Verdict**: Setup de qualité **{quality.value}** - Direction **{direction}**
"""
        return reasoning.strip()
    
    def _generate_action_plan(self, direction: str, quality: TradeQuality,
                              levels: Dict, urgency: str, 
                              entry_trigger: Dict = None) -> str:
        """Génère le plan d'action détaillé avec conditions d'entrée"""
        
        # SI WAIT = DONNER LES CONDITIONS POUR ENTRER
        if direction == "WAIT":
            wait_plan = """
🚫 **NE PAS TRADER MAINTENANT**

Les conditions ne sont pas réunies pour un trade rentable.

**Pourquoi attendre ?**
• Les tendances ne sont pas suffisamment alignées
• La qualité du setup n'est pas A+ ou A
• Le risque de perte est trop élevé
"""
            # Ajouter les conditions d'entrée future
            if entry_trigger and entry_trigger.get("order_type") == "LIMIT":
                wait_plan += f"""
**🎯 CONDITION D'ENTRÉE FUTURE (si le setup s'améliore):**

📌 **ORDRE LIMIT**: {entry_trigger.get('direction', 'LONG')} @ ${entry_trigger.get('price', 0):,.2f}
   • Condition: "{entry_trigger.get('condition', 'Attendre pullback')}"
   • Pattern détecté: {entry_trigger.get('pattern', 'Aucun')}
   
❌ **INVALIDE SI**: Prix casse ${entry_trigger.get('invalidation', 0):,.2f}
   • → Annuler l'ordre si ce niveau est cassé

⏰ **VALIDITÉ**: {entry_trigger.get('validity', '24h')}
"""
            else:
                wait_plan += """
**Que faire ?**
• Surveiller le marché
• Attendre un pullback vers un support/résistance clé
• Revérifier dans 1-4 heures

💡 **Conseil**: Mettre une alerte de prix sur le support/résistance le plus proche
"""
            wait_plan += """
⚠️ Trader sans setup de qualité = perdre de l'argent
"""
            return wait_plan
        
        if quality == TradeQuality.D:
            return "❌ **NE PAS TRADER** - Conditions non favorables. Attendez un meilleur setup."
        
        if quality == TradeQuality.C:
            return "⚠️ **NE PAS TRADER** - Setup de qualité C = trop risqué."
        
        if quality == TradeQuality.B:
            return "⚠️ **NE PAS TRADER** - Setup de qualité B = pas assez fiable."
        
        action = "ACHETER" if direction == "LONG" else "VENDRE" if direction == "SHORT" else "ATTENDRE"
        emoji = "🟢" if direction == "LONG" else "🔴" if direction == "SHORT" else "🟡"
        
        # Déterminer le type d'ordre
        order_type = "MARKET"
        entry_condition = "→ Entrée possible maintenant"
        
        if entry_trigger and entry_trigger.get("order_type") == "LIMIT":
            order_type = "LIMIT"
            entry_condition = f"""→ **ORDRE LIMIT RECOMMANDÉ**
   • Pattern: {entry_trigger.get('pattern', 'Signal technique')}
   • Condition: "{entry_trigger.get('condition', 'Attendre confirmation')}"
   • ❌ Invalide si: ${entry_trigger.get('invalidation', 0):,.2f}"""
        elif urgency == "WAIT_PULLBACK":
            entry_condition = "→ Attendre un pullback vers ce niveau"
        
        plan = f"""
{emoji} **PLAN D'ACTION - {action}**

📍 **ENTRÉE**: ${levels['entry']:,.2f} ({order_type})
   {entry_condition}

🛡️ **STOP LOSS**: ${levels['stop']:,.2f}
   → Risque: {levels['risk_percent']:.1f}%
   → OBLIGATOIRE - Ne jamais trader sans stop!

🎯 **TAKE PROFITS**:
   • TP1: ${levels['tp1']:,.2f} → Prendre 30% des profits
   • TP2: ${levels['tp2']:,.2f} → Prendre 40% des profits  
   • TP3: ${levels['tp3']:,.2f} → Laisser courir 30% restants

📈 **RATIO R:R**: 1:{levels['rr_ratio']:.1f}
📊 **GAIN POTENTIEL**: +{levels['potential_gain']:.1f}%

⏰ **TIMING**: {urgency.replace('_', ' ')}
"""
        
        # Ajouter info ordre LIMIT si applicable
        if order_type == "LIMIT" and entry_trigger:
            plan += f"""
🎯 **CONSEIL ORDRE LIMIT**:
   • Placer l'ordre à ${entry_trigger.get('price', levels['entry']):,.2f}
   • Validité: {entry_trigger.get('validity', '24h')}
   • Si le prix n'atteint pas ce niveau → pas de trade
"""
        
        if quality == TradeQuality.A_PLUS:
            plan += "\n💎 **SETUP A+** - Conditions exceptionnelles! Taille de position normale."
        elif quality == TradeQuality.A:
            plan += "\n✅ **SETUP A** - Excellentes conditions. Taille de position normale."
        else:
            plan += "\n📊 **SETUP B** - Bonnes conditions. Réduire légèrement la position."
        
        return plan.strip()
    
    async def scan_best_opportunities(self, symbols: List[str] = None) -> Dict:
        """
        🔍 Scanne le marché pour trouver les MEILLEURES opportunités
        Retourne uniquement les setups de qualité A+ et A
        """
        
        if symbols is None:
            symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK"]
        
        logger.info(f"🔍 Scan de {len(symbols)} actifs...")
        
        opportunities = []
        
        for symbol in symbols:
            try:
                recommendation = await self.get_trade_recommendation(symbol)
                
                if "error" not in recommendation:
                    quality = recommendation["recommendation"]["quality"]
                    
                    # Garder seulement A+ et A
                    if quality in ["A+", "A"]:
                        opportunities.append({
                            "symbol": symbol,
                            "quality": quality,
                            "direction": recommendation["recommendation"]["direction"],
                            "confidence": recommendation["recommendation"]["confidence"],
                            "urgency": recommendation["recommendation"]["urgency"],
                            "timeframe": recommendation["recommendation"].get("timeframe", "4H"),
                            "trade_type": recommendation["recommendation"].get("trade_type", "INTRADAY"),
                            "estimated_duration": recommendation["recommendation"].get("estimated_duration", "4 à 24 heures"),
                            "hold_time_min": recommendation["recommendation"].get("hold_time_min", "4 heures"),
                            "hold_time_max": recommendation["recommendation"].get("hold_time_max", "24 heures"),
                            "entry": recommendation["levels"]["entry"],
                            "stop": recommendation["levels"]["stop"],
                            "tp1": recommendation["levels"]["tp1"],
                            "rr_ratio": recommendation["levels"]["rr_ratio"],
                            "gain_potential": recommendation["levels"]["potential_gain"],
                            "signals": recommendation["signals"][:3],  # Top 3 signaux
                            "action_plan": recommendation["action_plan"]
                        })
                        
            except Exception as e:
                logger.error(f"Erreur scan {symbol}: {e}")
        
        # Trier par qualité puis confidence
        opportunities.sort(
            key=lambda x: (x["quality"] == "A+", x["confidence"]),
            reverse=True
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scanned": len(symbols),
            "opportunities_found": len(opportunities),
            "best_setups": opportunities,
            "message": self._generate_scan_summary(opportunities)
        }
    
    def _generate_scan_summary(self, opportunities: List[Dict]) -> str:
        """Génère un résumé du scan"""
        
        if not opportunities:
            return """
🔍 **SCAN TERMINÉ - AUCUN SETUP A+ ou A**

Le marché ne présente pas d'opportunités exceptionnelles en ce moment.
Recommandations:
• Attendre patiemment de meilleures conditions
• Ne forcez pas les trades
• La patience est la clé du trading gagnant

⏳ Rescannez dans quelques heures.
"""
        
        a_plus = [o for o in opportunities if o["quality"] == "A+"]
        a_grade = [o for o in opportunities if o["quality"] == "A"]
        
        summary = f"""
🎯 **SCAN TERMINÉ - {len(opportunities)} OPPORTUNITÉ(S) TROUVÉE(S)**

"""
        
        if a_plus:
            summary += f"💎 **SETUPS A+ ({len(a_plus)})** - EXCEPTIONNELS:\n"
            for o in a_plus:
                emoji = "🟢" if o["direction"] == "LONG" else "🔴"
                summary += f"   {emoji} **{o['symbol']}** - {o['direction']} @ ${o['entry']:,.2f} | TP: +{o['gain_potential']:.1f}% | R:R 1:{o['rr_ratio']}\n"
        
        if a_grade:
            summary += f"\n✅ **SETUPS A ({len(a_grade)})** - EXCELLENTS:\n"
            for o in a_grade:
                emoji = "🟢" if o["direction"] == "LONG" else "🔴"
                summary += f"   {emoji} **{o['symbol']}** - {o['direction']} @ ${o['entry']:,.2f} | TP: +{o['gain_potential']:.1f}% | R:R 1:{o['rr_ratio']}\n"
        
        summary += f"""
📌 **RECOMMANDATION**: Focalisez-vous sur le meilleur setup ({opportunities[0]['symbol']})
   Ne tradez pas tous en même temps - qualité > quantité!
"""
        
        return summary.strip()


# Instance globale
pro_trader = ProTraderAI()


