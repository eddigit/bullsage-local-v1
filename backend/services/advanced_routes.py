"""
Routes Avancées pour BULL SAGE
Endpoints pour les fonctionnalités d'optimisation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging

# Import des services
from services.technical_indicators import TechnicalIndicators, SignalGenerator, RiskManager
from services.telegram_notifier import TelegramNotifier
from services.auto_trader import AutoTrader, AutoTradeConfig
from services.backtester import backtester
from services.multi_timeframe import mtf_analyzer

logger = logging.getLogger(__name__)

# Router avancé
advanced_router = APIRouter(prefix="/api/advanced", tags=["Advanced Trading"])


# ==================== MODELS ====================

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    interval: str = "1h"
    initial_capital: float = 10000.0
    position_size_percent: float = 10.0
    stop_loss_percent: float = 2.0
    take_profit_percent: float = 4.0


class MTFAnalysisRequest(BaseModel):
    symbol: str
    timeframes: List[str] = ["1h", "4h", "1d"]


class TelegramConfigRequest(BaseModel):
    bot_token: str
    chat_id: str


class AutoTradeConfigRequest(BaseModel):
    symbol: str
    strategy: str = "rsi_macd"
    max_position_size_usd: float = 100.0
    stop_loss_percent: float = 2.0
    take_profit_percent: float = 4.0
    max_daily_trades: int = 3
    is_active: bool = True


class TradeAlertRequest(BaseModel):
    symbol: str
    action: str  # BUY, SELL
    price: float
    reason: str
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None


class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    prices: List[float]
    highs: Optional[List[float]] = None
    lows: Optional[List[float]] = None
    volumes: Optional[List[float]] = None


# ==================== INSTANCES ====================

indicators = TechnicalIndicators()
signal_generator = SignalGenerator()
risk_manager = RiskManager()
telegram_notifier = TelegramNotifier()
auto_trader = AutoTrader()


# ==================== HEALTH ====================

@advanced_router.get("/health")
async def advanced_health():
    """Vérifie l'état des services avancés"""
    return {
        "status": "healthy",
        "services": {
            "technical_indicators": True,
            "signal_generator": True,
            "backtester": True,
            "mtf_analyzer": True,
            "telegram_notifier": getattr(telegram_notifier, "enabled", False),
            "auto_trader": getattr(auto_trader, "enabled", False)
        }
    }


# ==================== TECHNICAL ANALYSIS ====================

@advanced_router.post("/indicators/calculate")
async def calculate_indicators(request: TechnicalAnalysisRequest):
    """Calcule tous les indicateurs techniques"""
    
    if len(request.prices) < 50:
        raise HTTPException(400, "Au moins 50 prix requis")
    
    result = indicators.calculate_all(
        prices=request.prices,
        highs=request.highs,
        lows=request.lows,
        volumes=request.volumes
    )
    
    return result


@advanced_router.get("/indicators/signal/{symbol}")
async def get_signal(symbol: str):
    """Génère un signal de trading pour un symbole"""
    
    # Récupérer les données depuis Kraken
    import aiohttp
    
    pair_map = {"BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD", "XRP": "XRPUSD"}
    pair = pair_map.get(symbol.upper(), f"{symbol.upper()}USD")
    
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=60"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    result = data.get("result", {})
                    for key in result:
                        if key != "last":
                            ohlc = result[key]
                            closes = [float(c[4]) for c in ohlc]
                            highs = [float(c[2]) for c in ohlc]
                            lows = [float(c[3]) for c in ohlc]
                            volumes = [float(c[6]) for c in ohlc]
                            
                            signal = signal_generator.analyze(
                                closes, highs, lows, volumes
                            )
                            
                            return {
                                "symbol": symbol,
                                "current_price": closes[-1],
                                **signal
                            }
    except Exception as e:
        logger.error(f"Erreur signal {symbol}: {e}")
        raise HTTPException(500, f"Erreur: {str(e)}")
    
    raise HTTPException(404, f"Données non disponibles pour {symbol}")


@advanced_router.post("/risk/position-size")
async def calculate_position_size(
    portfolio_value: float,
    entry_price: float,
    stop_loss_price: float,
    risk_percent: float = 1.0
):
    """Calcule la taille de position optimale"""
    
    result = risk_manager.calculate_position_size(
        portfolio_value=portfolio_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        risk_percent=risk_percent
    )
    
    return result


# ==================== BACKTESTING ====================

@advanced_router.get("/backtest/strategies")
async def list_strategies():
    """Liste les stratégies disponibles pour le backtest"""
    return {"strategies": backtester.get_available_strategies()}


@advanced_router.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Lance un backtest"""
    
    result = await backtester.run_backtest(
        symbol=request.symbol,
        strategy_name=request.strategy,
        interval=request.interval,
        initial_capital=request.initial_capital,
        position_size_percent=request.position_size_percent,
        stop_loss_percent=request.stop_loss_percent,
        take_profit_percent=request.take_profit_percent
    )
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


@advanced_router.get("/backtest/compare/{symbol}")
async def compare_strategies(symbol: str, interval: str = "1h"):
    """Compare toutes les stratégies sur un symbole"""
    
    results = []
    strategies = backtester.get_available_strategies()
    
    for strat in strategies:
        result = await backtester.run_backtest(
            symbol=symbol,
            strategy_name=strat["id"],
            interval=interval
        )
        
        if "error" not in result:
            results.append({
                "strategy": strat["name"],
                "total_return_percent": result["total_return_percent"],
                "win_rate": result["win_rate"],
                "profit_factor": result["profit_factor"],
                "max_drawdown_percent": result["max_drawdown_percent"],
                "sharpe_ratio": result["sharpe_ratio"],
                "total_trades": result["total_trades"]
            })
    
    # Trier par rendement
    results.sort(key=lambda x: x["total_return_percent"], reverse=True)
    
    return {"symbol": symbol, "comparisons": results}


# ==================== MULTI-TIMEFRAME ====================

@advanced_router.post("/mtf/analyze")
async def mtf_analyze(request: MTFAnalysisRequest):
    """Analyse multi-timeframe"""
    
    result = await mtf_analyzer.analyze(
        symbol=request.symbol,
        timeframes=request.timeframes
    )
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


@advanced_router.get("/mtf/opportunities")
async def get_opportunities(symbols: str = "BTC,ETH,SOL,XRP,ADA"):
    """Trouve les meilleures opportunités"""
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    opportunities = await mtf_analyzer.get_top_opportunities(symbol_list)
    
    return {"opportunities": opportunities}


@advanced_router.get("/mtf/quick/{symbol}")
async def quick_mtf_analysis(symbol: str):
    """Analyse MTF rapide"""
    
    result = await mtf_analyzer.analyze(symbol, ["1h", "4h", "1d"])
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


# ==================== TELEGRAM ====================

@advanced_router.post("/telegram/configure")
async def configure_telegram(config: TelegramConfigRequest):
    """Configure le bot Telegram"""
    
    telegram_notifier.configure(
        bot_token=config.bot_token,
        chat_id=config.chat_id
    )
    
    # Envoyer un message de test
    success = await telegram_notifier.send_message("🤖 BULL SAGE connecté à Telegram!")
    
    if success:
        return {"status": "configured", "test_message": "sent"}
    else:
        raise HTTPException(500, "Échec envoi message test")


@advanced_router.get("/telegram/status")
async def telegram_status():
    """Vérifie le statut Telegram"""
    return {
        "enabled": getattr(telegram_notifier, "enabled", False),
        "configured": telegram_notifier.bot_token is not None
    }


@advanced_router.post("/telegram/alert")
async def send_trade_alert(request: TradeAlertRequest):
    """Envoie une alerte de trade"""
    
    if not getattr(telegram_notifier, "enabled", False):
        raise HTTPException(400, "Telegram non configuré")
    
    success = await telegram_notifier.send_trade_alert(
        symbol=request.symbol,
        action=request.action,
        price=request.price,
        reason=request.reason,
        take_profit=request.take_profit,
        stop_loss=request.stop_loss
    )
    
    return {"sent": success}


@advanced_router.post("/telegram/test")
async def test_telegram():
    """Envoie un message de test"""
    
    if not getattr(telegram_notifier, "enabled", False):
        raise HTTPException(400, "Telegram non configuré")
    
    success = await telegram_notifier.send_message("🧪 Test depuis BULL SAGE")
    
    return {"sent": success}


# ==================== AUTO TRADING ====================

@advanced_router.get("/autotrader/status")
async def autotrader_status():
    """Statut de l'auto-trading"""
    return {
        "active_trades": len(auto_trader.active_trades),
        "configured_symbols": list(auto_trader.configs.keys()) if hasattr(auto_trader, 'configs') else [],
        "enabled": True
    }


@advanced_router.post("/autotrader/configure")
async def configure_autotrader(config: AutoTradeConfigRequest):
    """Configure l'auto-trader pour un symbole"""
    
    auto_config = AutoTradeConfig(
        symbol=config.symbol,
        strategy=config.strategy,
        max_position_size_usd=config.max_position_size_usd,
        stop_loss_percent=config.stop_loss_percent,
        take_profit_percent=config.take_profit_percent,
        max_daily_trades=config.max_daily_trades,
        is_active=config.is_active
    )
    
    auto_trader.configure_symbol(auto_config)
    
    return {"status": "configured", "config": auto_config.__dict__}


@advanced_router.post("/autotrader/start/{symbol}")
async def start_autotrader(symbol: str, background_tasks: BackgroundTasks):
    """Démarre l'auto-trading pour un symbole"""
    
    if symbol.upper() not in auto_trader.configs:
        raise HTTPException(400, f"Configurer d'abord {symbol}")
    
    # Démarrer en background
    background_tasks.add_task(auto_trader.start_monitoring, symbol.upper())
    
    return {"status": "started", "symbol": symbol.upper()}


@advanced_router.post("/autotrader/stop/{symbol}")
async def stop_autotrader(symbol: str):
    """Arrête l'auto-trading pour un symbole"""
    
    auto_trader.stop_monitoring(symbol.upper())
    
    return {"status": "stopped", "symbol": symbol.upper()}


@advanced_router.get("/autotrader/trades")
async def get_auto_trades():
    """Liste les trades automatiques"""
    
    trades = list(auto_trader.active_trades.values()) if hasattr(auto_trader, "active_trades") else []
    
    return {"trades": trades}


# ==================== DASHBOARD ====================

@advanced_router.get("/dashboard")
async def get_dashboard():
    """Données pour le dashboard avancé"""
    
    # Analyse rapide des principales cryptos
    symbols = ["BTC", "ETH", "SOL"]
    analyses = []
    
    for symbol in symbols:
        try:
            result = await mtf_analyzer.analyze(symbol, ["1h", "4h"])
            if "error" not in result:
                analyses.append({
                    "symbol": symbol,
                    "price": result["current_price"],
                    "bias": result["overall_bias"],
                    "score": result["confluence_score"]
                })
        except:
            pass
    
    return {
        "market_overview": analyses,
        "autotrader": {"active_trades": len(auto_trader.active_trades), "enabled": True},
        "telegram": {"enabled": getattr(telegram_notifier, "enabled", False)},
        "available_strategies": backtester.get_available_strategies()
    }




