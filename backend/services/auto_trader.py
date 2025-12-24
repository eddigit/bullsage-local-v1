"""
Service d'Auto-Trading pour BULL SAGE
Exécution automatique des signaux avec gestion de risque stricte
Mode Paper Trading uniquement pour la sécurité
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    STOPPED_OUT = "stopped_out"
    TAKE_PROFIT = "take_profit"


class TradeSide(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class AutoTradeConfig:
    """Configuration de l'auto-trading pour un utilisateur"""
    user_id: str
    enabled: bool = False
    max_position_size_percent: float = 5.0
    max_daily_trades: int = 10
    max_daily_loss_percent: float = 5.0
    min_confluence_score: float = 60.0
    allowed_symbols: List[str] = field(default_factory=lambda: ["BTC", "ETH", "SOL"])
    use_stop_loss: bool = True
    use_take_profit: bool = True
    risk_per_trade_percent: float = 1.0
    trailing_stop_enabled: bool = False
    trailing_stop_percent: float = 2.0


@dataclass
class AutoTrade:
    """Représente un trade automatique"""
    id: str
    user_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    position_value: float
    stop_loss: float
    take_profit: float
    status: str
    signal_score: float
    signal_reason: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    close_reason: Optional[str] = None


class AutoTrader:
    """Gestionnaire d'auto-trading sécurisé (Paper Trading)"""
    
    def __init__(self):
        self.db = None
        self.configs: Dict[str, AutoTradeConfig] = {}
        self.active_trades: Dict[str, List[AutoTrade]] = {}
        self.daily_stats: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self, db):
        """Initialise le service avec la base de données"""
        self.db = db
        
        if self.db:
            try:
                async for config_doc in self.db.auto_trade_configs.find({"enabled": True}):
                    user_id = config_doc.get("user_id")
                    if user_id:
                        self.configs[user_id] = AutoTradeConfig(
                            user_id=user_id,
                            enabled=config_doc.get("enabled", False),
                            max_position_size_percent=config_doc.get("max_position_size_percent", 5.0),
                            max_daily_trades=config_doc.get("max_daily_trades", 10),
                            max_daily_loss_percent=config_doc.get("max_daily_loss_percent", 5.0),
                            min_confluence_score=config_doc.get("min_confluence_score", 60.0),
                            allowed_symbols=config_doc.get("allowed_symbols", ["BTC", "ETH", "SOL"]),
                            risk_per_trade_percent=config_doc.get("risk_per_trade_percent", 1.0)
                        )
                logger.info(f"✅ AutoTrader initialisé avec {len(self.configs)} configurations")
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement configs auto-trade: {e}")
    
    async def configure_user(self, user_id: str, config: Dict) -> Dict:
        """Configure l'auto-trading pour un utilisateur avec validation de sécurité"""
        
        # Validation stricte des paramètres
        validated_config = {
            "user_id": user_id,
            "enabled": config.get("enabled", False),
            "max_position_size_percent": min(max(config.get("max_position_size_percent", 5.0), 1.0), 10.0),
            "max_daily_trades": min(max(config.get("max_daily_trades", 10), 1), 20),
            "max_daily_loss_percent": min(max(config.get("max_daily_loss_percent", 5.0), 1.0), 10.0),
            "min_confluence_score": max(config.get("min_confluence_score", 60.0), 50.0),
            "allowed_symbols": config.get("allowed_symbols", ["BTC", "ETH", "SOL"])[:10],
            "use_stop_loss": True,  # Toujours obligatoire
            "use_take_profit": config.get("use_take_profit", True),
            "risk_per_trade_percent": min(max(config.get("risk_per_trade_percent", 1.0), 0.5), 2.0),
            "trailing_stop_enabled": config.get("trailing_stop_enabled", False),
            "trailing_stop_percent": min(max(config.get("trailing_stop_percent", 2.0), 0.5), 5.0)
        }
        
        self.configs[user_id] = AutoTradeConfig(**validated_config)
        
        # Sauvegarder en base
        if self.db:
            try:
                await self.db.auto_trade_configs.update_one(
                    {"user_id": user_id},
                    {"$set": validated_config},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Erreur sauvegarde config: {e}")
        
        logger.info(f"✅ Configuration auto-trading mise à jour pour {user_id}")
        
        return {
            "success": True,
            "config": validated_config,
            "warnings": self._get_config_warnings(validated_config)
        }
    
    def _get_config_warnings(self, config: Dict) -> List[str]:
        """Génère des avertissements pour la configuration"""
        warnings = []
        
        if config["max_position_size_percent"] > 5:
            warnings.append("⚠️ Position > 5% du capital est risquée")
        
        if config["risk_per_trade_percent"] > 1:
            warnings.append("⚠️ Risque > 1% par trade peut éroder le capital")
        
        if config["min_confluence_score"] < 60:
            warnings.append("⚠️ Score < 60 peut générer des faux signaux")
        
        return warnings
    
    async def process_signal(self, 
                              user_id: str, 
                              symbol: str,
                              signal: Dict,
                              current_price: float) -> Dict:
        """Traite un signal de trading"""
        
        async with self._lock:
            # Vérifier si l'auto-trading est activé
            config = self.configs.get(user_id)
            if not config or not config.enabled:
                return {"action": "SKIP", "reason": "Auto-trading désactivé"}
            
            # Vérifier le symbole
            if symbol.upper() not in [s.upper() for s in config.allowed_symbols]:
                return {"action": "SKIP", "reason": f"{symbol} non autorisé"}
            
            # Vérifier le score
            score = signal.get("confluence_score", 0)
            if score < config.min_confluence_score:
                return {"action": "SKIP", "reason": f"Score {score:.1f} < minimum {config.min_confluence_score}"}
            
            # Vérifier les limites journalières
            daily_check = self._check_daily_limits(user_id, config)
            if not daily_check["allowed"]:
                return {"action": "SKIP", "reason": daily_check["reason"]}
            
            # Vérifier si position déjà ouverte
            if self._has_open_position(user_id, symbol):
                return {"action": "SKIP", "reason": f"Position déjà ouverte sur {symbol}"}
            
            # Calculer la position
            position = await self._calculate_position(user_id, config, current_price, signal)
            
            if position.get("error"):
                return {"action": "SKIP", "reason": position["error"]}
            
            # Exécuter le trade
            trade = await self._execute_trade(user_id, symbol, signal, position, current_price)
            
            return {
                "action": "EXECUTED",
                "trade": trade,
                "message": f"Trade {trade['side']} ouvert sur {symbol}"
            }
    
    def _check_daily_limits(self, user_id: str, config: AutoTradeConfig) -> Dict:
        """Vérifie les limites journalières"""
        today = datetime.utcnow().date().isoformat()
        
        if user_id not in self.daily_stats:
            self.daily_stats[user_id] = {}
        
        if today not in self.daily_stats[user_id]:
            self.daily_stats[user_id][today] = {
                "trades_count": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0
            }
        
        stats = self.daily_stats[user_id][today]
        
        if stats["trades_count"] >= config.max_daily_trades:
            return {"allowed": False, "reason": f"Limite de {config.max_daily_trades} trades/jour atteinte"}
        
        if stats["total_pnl_percent"] <= -config.max_daily_loss_percent:
            return {"allowed": False, "reason": f"Perte max ({config.max_daily_loss_percent}%) atteinte"}
        
        return {"allowed": True}
    
    def _has_open_position(self, user_id: str, symbol: str) -> bool:
        """Vérifie si une position est déjà ouverte"""
        if user_id not in self.active_trades:
            return False
        
        for trade in self.active_trades[user_id]:
            if trade.symbol.upper() == symbol.upper() and trade.status == "open":
                return True
        
        return False
    
    async def _calculate_position(self, 
                                    user_id: str, 
                                    config: AutoTradeConfig,
                                    current_price: float,
                                    signal: Dict) -> Dict:
        """Calcule la taille de position"""
        
        # Récupérer le capital
        capital = 10000.0
        if self.db:
            try:
                user = await self.db.users.find_one({"id": user_id})
                if user:
                    capital = user.get("paper_balance", 10000.0)
            except Exception:
                pass
        
        # Risque par trade
        risk_amount = capital * (config.risk_per_trade_percent / 100)
        
        # Stop loss
        stop_loss_percent = signal.get("stop_loss_percent", 2.0)
        stop_loss_price = current_price * (1 - stop_loss_percent / 100)
        
        price_risk = abs(current_price - stop_loss_price)
        
        if price_risk == 0:
            return {"error": "Stop loss invalide"}
        
        # Taille de position
        quantity = risk_amount / price_risk
        position_value = quantity * current_price
        
        # Limiter à la taille max
        max_position_value = capital * (config.max_position_size_percent / 100)
        if position_value > max_position_value:
            quantity = max_position_value / current_price
            position_value = max_position_value
        
        # Take profit
        take_profit_percent = signal.get("take_profit_percent", stop_loss_percent * 2)
        take_profit_price = current_price * (1 + take_profit_percent / 100)
        
        return {
            "quantity": round(quantity, 6),
            "position_value": round(position_value, 2),
            "stop_loss": round(stop_loss_price, 2),
            "take_profit": round(take_profit_price, 2),
            "risk_amount": round(risk_amount, 2),
            "capital": capital
        }
    
    async def _execute_trade(self,
                              user_id: str,
                              symbol: str,
                              signal: Dict,
                              position: Dict,
                              current_price: float) -> Dict:
        """Exécute un trade Paper Trading"""
        
        trade_id = str(uuid.uuid4())
        side = "long" if signal.get("direction") == "BULLISH" else "short"
        
        trade = AutoTrade(
            id=trade_id,
            user_id=user_id,
            symbol=symbol.upper(),
            side=side,
            entry_price=current_price,
            quantity=position["quantity"],
            position_value=position["position_value"],
            stop_loss=position["stop_loss"],
            take_profit=position["take_profit"],
            status="open",
            signal_score=signal.get("confluence_score", 0),
            signal_reason=signal.get("reason", "Signal automatique"),
            created_at=datetime.utcnow()
        )
        
        # Ajouter à la liste active
        if user_id not in self.active_trades:
            self.active_trades[user_id] = []
        self.active_trades[user_id].append(trade)
        
        # Sauvegarder en base
        if self.db:
            try:
                await self.db.auto_trades.insert_one({
                    "id": trade_id,
                    "user_id": user_id,
                    "symbol": symbol.upper(),
                    "side": side,
                    "entry_price": current_price,
                    "quantity": position["quantity"],
                    "position_value": position["position_value"],
                    "stop_loss": position["stop_loss"],
                    "take_profit": position["take_profit"],
                    "status": "open",
                    "signal_score": signal.get("confluence_score", 0),
                    "signal_reason": signal.get("reason", "Signal automatique"),
                    "created_at": datetime.utcnow()
                })
                
                # Déduire du capital
                await self.db.users.update_one(
                    {"id": user_id},
                    {"$inc": {"paper_balance": -position["position_value"]}}
                )
            except Exception as e:
                logger.error(f"Erreur sauvegarde trade: {e}")
        
        # Stats journalières
        today = datetime.utcnow().date().isoformat()
        if user_id in self.daily_stats and today in self.daily_stats[user_id]:
            self.daily_stats[user_id][today]["trades_count"] += 1
        
        logger.info(f"✅ Trade ouvert: {side} {symbol} @ ${current_price}")
        
        return {
            "id": trade_id,
            "symbol": symbol.upper(),
            "side": side,
            "entry_price": current_price,
            "quantity": position["quantity"],
            "position_value": position["position_value"],
            "stop_loss": position["stop_loss"],
            "take_profit": position["take_profit"]
        }
    
    async def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> List[Dict]:
        """Vérifie les SL/TP pour tous les trades actifs"""
        
        closed_trades = []
        
        for user_id, trades in self.active_trades.items():
            for trade in trades:
                if trade.symbol.upper() != symbol.upper() or trade.status != "open":
                    continue
                
                should_close = False
                close_reason = ""
                
                if trade.side == "long":
                    if current_price <= trade.stop_loss:
                        should_close = True
                        close_reason = "STOP_LOSS"
                    elif current_price >= trade.take_profit:
                        should_close = True
                        close_reason = "TAKE_PROFIT"
                else:
                    if current_price >= trade.stop_loss:
                        should_close = True
                        close_reason = "STOP_LOSS"
                    elif current_price <= trade.take_profit:
                        should_close = True
                        close_reason = "TAKE_PROFIT"
                
                if should_close:
                    result = await self._close_trade(trade, current_price, close_reason)
                    closed_trades.append(result)
        
        return closed_trades
    
    async def _close_trade(self, trade: AutoTrade, exit_price: float, reason: str) -> Dict:
        """Ferme un trade"""
        
        # Calculer P&L
        if trade.side == "long":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity
        
        pnl_percent = (pnl / trade.position_value) * 100
        
        # Mettre à jour le trade
        trade.status = "stopped_out" if reason == "STOP_LOSS" else "take_profit"
        trade.exit_price = exit_price
        trade.closed_at = datetime.utcnow()
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.close_reason = reason
        
        # Mettre à jour en base
        if self.db:
            try:
                await self.db.auto_trades.update_one(
                    {"id": trade.id},
                    {"$set": {
                        "status": trade.status,
                        "exit_price": exit_price,
                        "closed_at": trade.closed_at,
                        "pnl": pnl,
                        "pnl_percent": pnl_percent,
                        "close_reason": reason
                    }}
                )
                
                # Rendre le capital + P&L
                await self.db.users.update_one(
                    {"id": trade.user_id},
                    {"$inc": {"paper_balance": trade.position_value + pnl}}
                )
            except Exception as e:
                logger.error(f"Erreur fermeture trade: {e}")
        
        # Stats journalières
        today = datetime.utcnow().date().isoformat()
        if trade.user_id in self.daily_stats and today in self.daily_stats[trade.user_id]:
            self.daily_stats[trade.user_id][today]["total_pnl"] += pnl
        
        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"{emoji} Trade fermé: {trade.symbol} - P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
        
        return {
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": exit_price,
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "reason": reason
        }
    
    async def get_user_trades(self, user_id: str, status: str = None) -> List[Dict]:
        """Récupère les trades d'un utilisateur"""
        
        if self.db:
            try:
                query = {"user_id": user_id}
                if status:
                    query["status"] = status
                
                trades = await self.db.auto_trades.find(
                    query, {"_id": 0}
                ).sort("created_at", -1).to_list(100)
                return trades
            except Exception as e:
                logger.error(f"Erreur récupération trades: {e}")
        
        return []
    
    async def get_user_stats(self, user_id: str) -> Dict:
        """Récupère les statistiques de trading"""
        
        if not self.db:
            return {"error": "Base de données non disponible"}
        
        try:
            closed_trades = await self.db.auto_trades.find({
                "user_id": user_id,
                "status": {"$in": ["stopped_out", "take_profit", "closed"]}
            }).to_list(1000)
            
            if not closed_trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0
                }
            
            winning = [t for t in closed_trades if t.get("pnl", 0) > 0]
            losing = [t for t in closed_trades if t.get("pnl", 0) < 0]
            total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
            
            return {
                "total_trades": len(closed_trades),
                "winning_trades": len(winning),
                "losing_trades": len(losing),
                "win_rate": round((len(winning) / len(closed_trades)) * 100, 2),
                "total_pnl": round(total_pnl, 2),
                "average_pnl": round(total_pnl / len(closed_trades), 2)
            }
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return {"error": str(e)}


# Instance globale
auto_trader = AutoTrader()
