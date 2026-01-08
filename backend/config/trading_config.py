"""
Configuration Trading pour Bull Sage
=====================================

Ce fichier centralise tous les parametres de trading et de securite
pour l'automatisation via webhooks et l'execution sur dYdX.
"""

import os
from typing import List, Dict
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """Niveaux de risque pour les trades"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TradeType(Enum):
    """Types de trades supportes"""
    SCALPING = "SCALPING"
    INTRADAY = "INTRADAY"
    INTRADAY_PLUS = "INTRADAY+"
    SWING = "SWING"
    POSITION = "POSITION"


@dataclass
class TradingConfig:
    """Configuration principale du trading"""

    # === RISK MANAGEMENT ===
    MAX_RISK_PERCENT: float = 2.0  # Risque max par trade (% du capital)
    MAX_DAILY_RISK_PERCENT: float = 6.0  # Risque max journalier
    MAX_LEVERAGE: int = 10  # Levier maximum autorise
    MIN_CONFIDENCE: int = 80  # Score de confiance minimum (0-100)

    # === POSITION SIZING ===
    DEFAULT_POSITION_SIZE_PERCENT: float = 2.0  # Taille par defaut (% du capital)
    MAX_POSITION_SIZE_PERCENT: float = 10.0  # Taille max d'une position
    MAX_OPEN_POSITIONS: int = 5  # Nombre max de positions ouvertes

    # === SLIPPAGE & EXECUTION ===
    MAX_SLIPPAGE_PERCENT: float = 1.0  # Slippage max accepte
    TRADE_COOLDOWN_SECONDS: int = 60  # Delai entre trades sur meme marche
    ORDER_TIMEOUT_SECONDS: int = 30  # Timeout pour l'execution

    # === MARCHES AUTORISES ===
    ALLOWED_MARKETS: List[str] = field(default_factory=lambda: [
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
        "AVAX-USD",
        "DOGE-USD",
        "XRP-USD",
        "ADA-USD",
        "DOT-USD",
        "LINK-USD",
        "MATIC-USD"
    ])

    # === STOP LOSS OBLIGATOIRE ===
    REQUIRE_STOP_LOSS: bool = True
    MIN_STOP_LOSS_PERCENT: float = 1.0  # SL minimum (% du prix d'entree)
    MAX_STOP_LOSS_PERCENT: float = 15.0  # SL maximum (% du prix d'entree)

    # === TAKE PROFIT ===
    REQUIRE_TAKE_PROFIT: bool = False
    DEFAULT_RISK_REWARD_RATIO: float = 2.0  # Ratio R:R par defaut

    # === FILTRES DE QUALITE ===
    MIN_SIGNAL_GRADE: str = "A"  # Grade minimum (A+, A, B+, B, C)
    ALLOWED_GRADES: List[str] = field(default_factory=lambda: ["A+", "A"])

    # === HEURES DE TRADING ===
    TRADING_ENABLED: bool = True
    TRADING_HOURS_UTC: Dict[str, int] = field(default_factory=lambda: {
        "start": 0,  # 00:00 UTC (crypto = 24/7)
        "end": 24
    })

    # === WEBHOOK SECURITY ===
    WEBHOOK_RATE_LIMIT: int = 10  # Requetes max par minute
    WEBHOOK_TOKEN_REQUIRED: bool = True

    # === LOGGING ===
    LOG_ALL_TRADES: bool = True
    LOG_WEBHOOK_CALLS: bool = True

    def is_market_allowed(self, market: str) -> bool:
        """Verifie si un marche est autorise"""
        return market in self.ALLOWED_MARKETS

    def is_confidence_sufficient(self, confidence: float) -> bool:
        """Verifie si le score de confiance est suffisant"""
        return confidence >= self.MIN_CONFIDENCE

    def is_grade_allowed(self, grade: str) -> bool:
        """Verifie si le grade est autorise"""
        return grade in self.ALLOWED_GRADES

    def calculate_position_size(self, equity: float, risk_percent: float = None) -> float:
        """Calcule la taille de position basee sur le risque"""
        risk = risk_percent or self.DEFAULT_POSITION_SIZE_PERCENT
        risk = min(risk, self.MAX_POSITION_SIZE_PERCENT)
        return equity * (risk / 100)

    def validate_stop_loss(self, entry_price: float, stop_loss: float, direction: str) -> Dict:
        """Valide le stop loss"""
        if not stop_loss:
            if self.REQUIRE_STOP_LOSS:
                return {"valid": False, "error": "Stop loss obligatoire"}
            return {"valid": True}

        if direction == "LONG":
            sl_percent = ((entry_price - stop_loss) / entry_price) * 100
            if stop_loss >= entry_price:
                return {"valid": False, "error": "SL doit etre < prix d'entree pour LONG"}
        else:  # SHORT
            sl_percent = ((stop_loss - entry_price) / entry_price) * 100
            if stop_loss <= entry_price:
                return {"valid": False, "error": "SL doit etre > prix d'entree pour SHORT"}

        if sl_percent < self.MIN_STOP_LOSS_PERCENT:
            return {"valid": False, "error": f"SL trop serre (min {self.MIN_STOP_LOSS_PERCENT}%)"}

        if sl_percent > self.MAX_STOP_LOSS_PERCENT:
            return {"valid": False, "error": f"SL trop large (max {self.MAX_STOP_LOSS_PERCENT}%)"}

        return {"valid": True, "sl_percent": sl_percent}

    def calculate_risk_amount(self, position_size: float, entry_price: float,
                               stop_loss: float, direction: str) -> float:
        """Calcule le montant a risque"""
        if direction == "LONG":
            risk_per_unit = entry_price - stop_loss
        else:
            risk_per_unit = stop_loss - entry_price

        return position_size * risk_per_unit


# Instance globale de configuration
trading_config = TradingConfig()


# Charger les overrides depuis les variables d'environnement
def load_config_from_env():
    """Charge la configuration depuis les variables d'environnement"""
    global trading_config

    if os.getenv("MAX_RISK_PERCENT"):
        trading_config.MAX_RISK_PERCENT = float(os.getenv("MAX_RISK_PERCENT"))

    if os.getenv("MAX_LEVERAGE"):
        trading_config.MAX_LEVERAGE = int(os.getenv("MAX_LEVERAGE"))

    if os.getenv("MIN_CONFIDENCE"):
        trading_config.MIN_CONFIDENCE = int(os.getenv("MIN_CONFIDENCE"))

    if os.getenv("MAX_SLIPPAGE_PERCENT"):
        trading_config.MAX_SLIPPAGE_PERCENT = float(os.getenv("MAX_SLIPPAGE_PERCENT"))

    if os.getenv("TRADE_COOLDOWN_SECONDS"):
        trading_config.TRADE_COOLDOWN_SECONDS = int(os.getenv("TRADE_COOLDOWN_SECONDS"))

    if os.getenv("ALLOWED_MARKETS"):
        trading_config.ALLOWED_MARKETS = os.getenv("ALLOWED_MARKETS").split(",")

    if os.getenv("TRADING_ENABLED"):
        trading_config.TRADING_ENABLED = os.getenv("TRADING_ENABLED").lower() == "true"


# Charger au demarrage
load_config_from_env()


# Export des constantes pour compatibilite
MAX_RISK_PERCENT = trading_config.MAX_RISK_PERCENT
MAX_LEVERAGE = trading_config.MAX_LEVERAGE
MIN_CONFIDENCE = trading_config.MIN_CONFIDENCE
ALLOWED_MARKETS = trading_config.ALLOWED_MARKETS
TRADE_COOLDOWN_SECONDS = trading_config.TRADE_COOLDOWN_SECONDS
MAX_SLIPPAGE_PERCENT = trading_config.MAX_SLIPPAGE_PERCENT
