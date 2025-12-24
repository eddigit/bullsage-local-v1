"""
Service de Backtesting pour BULL SAGE
Teste les stratégies sur données historiques
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import logging

from services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Trade dans le backtest"""
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    side: str = "long"
    quantity: float = 0
    pnl: float = 0
    pnl_percent: float = 0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """Résultat du backtest"""
    symbol: str
    strategy: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    max_drawdown_percent: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_pnl: float
    sharpe_ratio: float
    trades: List[Dict]
    equity_curve: List[float]


class Strategy:
    """Classe de base pour les stratégies"""
    
    def __init__(self, name: str = "Base Strategy"):
        self.name = name
        self.indicators = TechnicalIndicators()
    
    def generate_signal(self, 
                        prices: List[float],
                        highs: List[float],
                        lows: List[float],
                        volumes: List[float],
                        index: int) -> Optional[str]:
        """Génère un signal (BUY, SELL, ou None)"""
        raise NotImplementedError


class RSIMACDStrategy(Strategy):
    """Stratégie RSI + MACD"""
    
    def __init__(self, rsi_oversold: float = 30, rsi_overbought: float = 70):
        super().__init__("RSI + MACD")
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_signal(self, prices, highs, lows, volumes, index) -> Optional[str]:
        if index < 50:
            return None
        
        rsi = self.indicators.calculate_rsi(prices[:index+1])
        macd = self.indicators.calculate_macd(prices[:index+1])
        
        if rsi < self.rsi_oversold and macd["histogram"] > 0:
            return "BUY"
        
        if rsi > self.rsi_overbought and macd["histogram"] < 0:
            return "SELL"
        
        return None


class BollingerRSIStrategy(Strategy):
    """Stratégie Bollinger + RSI"""
    
    def __init__(self):
        super().__init__("Bollinger + RSI")
    
    def generate_signal(self, prices, highs, lows, volumes, index) -> Optional[str]:
        if index < 50:
            return None
        
        current_price = prices[index]
        bb = self.indicators.calculate_bollinger_bands(prices[:index+1])
        rsi = self.indicators.calculate_rsi(prices[:index+1])
        
        if current_price < bb["lower"] and rsi < 35:
            return "BUY"
        
        if current_price > bb["upper"] and rsi > 65:
            return "SELL"
        
        return None


class TripleEMAStrategy(Strategy):
    """Stratégie Triple EMA"""
    
    def __init__(self, fast: int = 8, medium: int = 21, slow: int = 55):
        super().__init__("Triple EMA")
        self.fast = fast
        self.medium = medium
        self.slow = slow
    
    def generate_signal(self, prices, highs, lows, volumes, index) -> Optional[str]:
        if index < self.slow + 5:
            return None
        
        ema_fast = self.indicators.calculate_ema(prices[:index+1], self.fast)
        ema_medium = self.indicators.calculate_ema(prices[:index+1], self.medium)
        ema_slow = self.indicators.calculate_ema(prices[:index+1], self.slow)
        
        # Calculer EMA précédente
        ema_fast_prev = self.indicators.calculate_ema(prices[:index], self.fast)
        ema_medium_prev = self.indicators.calculate_ema(prices[:index], self.medium)
        
        if ema_fast > ema_medium > ema_slow:
            if ema_fast_prev <= ema_medium_prev:
                return "BUY"
        
        if ema_fast < ema_medium < ema_slow:
            if ema_fast_prev >= ema_medium_prev:
                return "SELL"
        
        return None


class Backtester:
    """Moteur de backtesting"""
    
    KRAKEN_INTERVALS = {
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }
    
    SYMBOL_MAP = {
        "BTC": "XBTUSD",
        "ETH": "ETHUSD",
        "SOL": "SOLUSD",
        "XRP": "XRPUSD"
    }
    
    def __init__(self):
        self.strategies = {
            "rsi_macd": RSIMACDStrategy(),
            "bollinger_rsi": BollingerRSIStrategy(),
            "triple_ema": TripleEMAStrategy()
        }
    
    async def fetch_historical_data(self, symbol: str, interval: str = "1h") -> Optional[Dict]:
        """Récupère les données historiques depuis Kraken"""
        
        pair = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}USD")
        kraken_interval = self.KRAKEN_INTERVALS.get(interval, 60)
        
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={kraken_interval}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("error") and len(data["error"]) > 0:
                            logger.error(f"Erreur Kraken: {data['error']}")
                            return None
                        
                        result = data.get("result", {})
                        for key in result:
                            if key != "last":
                                ohlc_data = result[key]
                                return self._parse_ohlc(ohlc_data)
        except Exception as e:
            logger.error(f"Erreur fetch données: {e}")
        
        return None
    
    def _parse_ohlc(self, data: List) -> Dict:
        """Parse les données OHLC"""
        timestamps = [datetime.fromtimestamp(candle[0]) for candle in data]
        opens = [float(candle[1]) for candle in data]
        highs = [float(candle[2]) for candle in data]
        lows = [float(candle[3]) for candle in data]
        closes = [float(candle[4]) for candle in data]
        volumes = [float(candle[6]) for candle in data]
        
        return {
            "timestamps": timestamps,
            "opens": opens,
            "highs": highs,
            "lows": lows,
            "closes": closes,
            "volumes": volumes
        }
    
    async def run_backtest(self,
                           symbol: str,
                           strategy_name: str,
                           interval: str = "1h",
                           initial_capital: float = 10000.0,
                           position_size_percent: float = 10.0,
                           stop_loss_percent: float = 2.0,
                           take_profit_percent: float = 4.0) -> Dict:
        """Exécute un backtest complet"""
        
        logger.info(f"🔄 Démarrage backtest {strategy_name} sur {symbol}")
        
        # Récupérer les données
        data = await self.fetch_historical_data(symbol, interval)
        
        if not data or len(data["closes"]) < 100:
            return {"error": f"Pas assez de données pour {symbol}"}
        
        # Récupérer la stratégie
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return {"error": f"Stratégie inconnue: {strategy_name}"}
        
        # Exécuter la simulation
        result = self._run_simulation(
            data=data,
            strategy=strategy,
            initial_capital=initial_capital,
            position_size_percent=position_size_percent,
            stop_loss_percent=stop_loss_percent,
            take_profit_percent=take_profit_percent
        )
        
        logger.info(f"✅ Backtest terminé: {result['total_trades']} trades, ROI: {result['total_return_percent']:.2f}%")
        
        return {
            "symbol": symbol,
            "strategy": strategy_name,
            **result
        }
    
    def _run_simulation(self, 
                        data: Dict, 
                        strategy: Strategy,
                        initial_capital: float,
                        position_size_percent: float,
                        stop_loss_percent: float,
                        take_profit_percent: float) -> Dict:
        """Simule les trades"""
        
        prices = data["closes"]
        highs = data["highs"]
        lows = data["lows"]
        volumes = data["volumes"]
        timestamps = data["timestamps"]
        
        capital = initial_capital
        position = None
        trades = []
        equity_curve = [capital]
        
        for i in range(50, len(prices)):
            current_price = prices[i]
            current_time = timestamps[i]
            
            # Si position ouverte, vérifier SL/TP
            if position:
                exit_price = None
                exit_reason = ""
                
                if position["side"] == "long":
                    if current_price <= position["stop_loss"]:
                        exit_price = position["stop_loss"]
                        exit_reason = "STOP_LOSS"
                    elif current_price >= position["take_profit"]:
                        exit_price = position["take_profit"]
                        exit_reason = "TAKE_PROFIT"
                
                if exit_price:
                    pnl = (exit_price - position["entry_price"]) * position["quantity"]
                    pnl_percent = (pnl / (position["entry_price"] * position["quantity"])) * 100
                    
                    trades.append({
                        "entry_date": position["entry_time"].isoformat(),
                        "entry_price": position["entry_price"],
                        "exit_date": current_time.isoformat(),
                        "exit_price": exit_price,
                        "side": position["side"],
                        "quantity": position["quantity"],
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_percent, 2),
                        "exit_reason": exit_reason
                    })
                    
                    capital += position["entry_price"] * position["quantity"] + pnl
                    position = None
            
            # Si pas de position, chercher un signal
            if not position:
                signal = strategy.generate_signal(prices, highs, lows, volumes, i)
                
                if signal == "BUY":
                    position_value = capital * (position_size_percent / 100)
                    quantity = position_value / current_price
                    
                    position = {
                        "side": "long",
                        "entry_price": current_price,
                        "entry_time": current_time,
                        "quantity": quantity,
                        "stop_loss": current_price * (1 - stop_loss_percent / 100),
                        "take_profit": current_price * (1 + take_profit_percent / 100)
                    }
                    
                    capital -= position_value
            
            # Équité actuelle
            if position:
                unrealized = (current_price - position["entry_price"]) * position["quantity"]
                equity = capital + position["entry_price"] * position["quantity"] + unrealized
            else:
                equity = capital
            
            equity_curve.append(equity)
        
        # Fermer position restante
        if position:
            final_price = prices[-1]
            pnl = (final_price - position["entry_price"]) * position["quantity"]
            
            trades.append({
                "entry_date": position["entry_time"].isoformat(),
                "entry_price": position["entry_price"],
                "exit_date": timestamps[-1].isoformat(),
                "exit_price": final_price,
                "side": position["side"],
                "quantity": position["quantity"],
                "pnl": round(pnl, 2),
                "pnl_percent": round((pnl / (position["entry_price"] * position["quantity"])) * 100, 2),
                "exit_reason": "END_OF_DATA"
            })
            capital += position["entry_price"] * position["quantity"] + pnl
        
        # Calculer statistiques
        return self._calculate_statistics(initial_capital, capital, trades, equity_curve)
    
    def _calculate_statistics(self, initial_capital: float, final_capital: float, 
                               trades: List[Dict], equity_curve: List[float]) -> Dict:
        """Calcule les statistiques"""
        
        total_return = final_capital - initial_capital
        total_return_percent = (total_return / initial_capital) * 100
        
        # Drawdown
        peak = initial_capital
        max_dd_percent = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd_percent:
                max_dd_percent = dd
        
        # Stats trades
        winning = [t for t in trades if t["pnl"] > 0]
        losing = [t for t in trades if t["pnl"] < 0]
        
        total_trades = len(trades)
        win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sum(t["pnl"] for t in winning) if winning else 0
        gross_loss = abs(sum(t["pnl"] for t in losing)) if losing else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999
        
        avg_pnl = (total_return / total_trades) if total_trades > 0 else 0
        
        # Sharpe
        if len(equity_curve) > 1:
            returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        return {
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": round(total_return, 2),
            "total_return_percent": round(total_return_percent, 2),
            "max_drawdown_percent": round(max_dd_percent, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(min(profit_factor, 999), 2),
            "total_trades": total_trades,
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "avg_trade_pnl": round(avg_pnl, 2),
            "sharpe_ratio": round(sharpe, 2),
            "trades": trades[-20:],  # Derniers 20 trades
            "equity_curve": equity_curve[::max(1, len(equity_curve)//100)]  # 100 points max
        }
    
    def get_available_strategies(self) -> List[Dict]:
        """Liste des stratégies disponibles"""
        return [
            {"id": "rsi_macd", "name": "RSI + MACD", "description": "RSI survendu/suracheté + MACD"},
            {"id": "bollinger_rsi", "name": "Bollinger + RSI", "description": "Bandes de Bollinger + RSI"},
            {"id": "triple_ema", "name": "Triple EMA", "description": "3 moyennes mobiles exponentielles"}
        ]


# Instance globale
backtester = Backtester()
