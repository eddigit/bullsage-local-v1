from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import logging
import httpx

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import PaperTrade, PaperTradeCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/paper-trading", tags=["Paper Trading"])

# Cache des prix pour éviter les appels API répétés
_price_cache = {}
_price_cache_time = None

async def get_current_prices():
    """Récupère les prix actuels des cryptos"""
    global _price_cache, _price_cache_time
    
    # Cache de 30 secondes
    if _price_cache_time and (datetime.now(timezone.utc) - _price_cache_time).seconds < 30:
        return _price_cache
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://min-api.cryptocompare.com/data/top/mktcapfull",
                params={"limit": 50, "tsym": "USD"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for item in data.get("Data", []):
                    coin_info = item.get("CoinInfo", {})
                    raw = item.get("RAW", {}).get("USD", {})
                    symbol = coin_info.get("Name", "").lower()
                    coin_id = f"{symbol}"
                    prices[coin_id] = {
                        "price": raw.get("PRICE", 0),
                        "change_24h": raw.get("CHANGEPCT24HOUR", 0),
                        "name": coin_info.get("FullName", symbol)
                    }
                    # Aussi stocker avec le format bitcoin, ethereum, etc.
                    full_name = coin_info.get("FullName", "").lower().replace(" ", "-")
                    prices[full_name] = prices[coin_id]
                _price_cache = prices
                _price_cache_time = datetime.now(timezone.utc)
                return prices
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
    
    return _price_cache

@router.post("/trade", response_model=PaperTrade)
async def execute_paper_trade(trade: PaperTradeCreate, current_user: dict = Depends(get_current_user)):
    """Execute a paper trade"""
    user_id = current_user["id"]
    
    # Valider le montant
    if trade.amount <= 0:
        raise HTTPException(status_code=400, detail="La quantité doit être positive")
    
    user = await db.users.find_one({"id": user_id})
    balance = user.get("paper_balance", 10000.0)
    portfolio = user.get("portfolio", {})
    
    total_cost = trade.amount * trade.price
    
    if trade.type == "buy":
        if total_cost > balance:
            raise HTTPException(status_code=400, detail="Solde insuffisant")
        
        new_balance = balance - total_cost
        current_holding = portfolio.get(trade.symbol, {"amount": 0, "avg_price": 0, "entry_date": None})
        
        total_amount = current_holding["amount"] + trade.amount
        if total_amount > 0:
            new_avg_price = ((current_holding["amount"] * current_holding.get("avg_price", 0)) + total_cost) / total_amount
        else:
            new_avg_price = trade.price
        
        # Stocker la date d'entrée (première fois qu'on achète)
        entry_date = current_holding.get("entry_date") or datetime.now(timezone.utc).isoformat()
        
        portfolio[trade.symbol] = {
            "amount": total_amount, 
            "avg_price": new_avg_price,
            "entry_date": entry_date,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    elif trade.type == "sell":
        current_holding = portfolio.get(trade.symbol, {"amount": 0})
        current_amount = current_holding.get("amount", 0)
        
        if current_amount < trade.amount:
            raise HTTPException(status_code=400, detail=f"Position insuffisante. Vous avez {current_amount:.6f} {trade.symbol}")
        
        new_balance = balance + total_cost
        remaining = current_amount - trade.amount
        
        if remaining > 0.00000001:  # Éviter les problèmes de floating point
            portfolio[trade.symbol] = {
                "amount": remaining, 
                "avg_price": current_holding.get("avg_price", trade.price),
                "entry_date": current_holding.get("entry_date"),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Position fermée
            portfolio.pop(trade.symbol, None)
    else:
        raise HTTPException(status_code=400, detail="Type de trade invalide")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"paper_balance": new_balance, "portfolio": portfolio}}
    )
    
    trade_id = str(uuid.uuid4())
    trade_doc = {
        "id": trade_id,
        "user_id": user_id,
        "symbol": trade.symbol,
        "type": trade.type,
        "amount": trade.amount,
        "price": trade.price,
        "total_value": total_cost,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "executed"
    }
    await db.paper_trades.insert_one(trade_doc)
    
    return PaperTrade(**trade_doc)

@router.get("/trades")
async def get_paper_trades(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get paper trading history"""
    try:
        user_id = current_user["id"]
        logger.info(f"Fetching trades for user: {user_id}")
        
        trades = await db.paper_trades.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        logger.info(f"Found {len(trades)} trades for user: {user_id}")
        
        # Always return a list
        return trades if trades else []
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        return []

@router.get("/portfolio")
async def get_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Get paper trading portfolio with real-time prices and P&L"""
    try:
        user = await db.users.find_one({"id": current_user["id"]})
        if not user:
            logger.warning(f"User not found for portfolio: {current_user['id']}")
            return {
                "balance": 10000.0,
                "portfolio": {},
                "positions": [],
                "initial_balance": 10000.0,
                "total_value": 10000.0,
                "total_pnl": 0,
                "total_pnl_percent": 0
            }
        
        portfolio = user.get("portfolio", {})
        balance = user.get("paper_balance", 10000.0)
        
        # Récupérer les prix actuels
        current_prices = await get_current_prices()
        
        # Calculer les positions avec P&L en temps réel
        positions = []
        total_holdings_value = 0
        total_cost_basis = 0
        
        for symbol, holding in portfolio.items():
            amount = holding.get("amount", 0)
            avg_price = holding.get("avg_price", 0)
            entry_date = holding.get("entry_date")
            
            # Ignorer les positions négatives ou nulles
            if amount <= 0:
                continue
            
            # Chercher le prix actuel (essayer plusieurs formats)
            current_price = 0
            symbol_lower = symbol.lower()
            
            # Chercher dans le cache de prix
            if symbol_lower in current_prices:
                current_price = current_prices[symbol_lower].get("price", 0)
            elif symbol_lower.replace("-", "") in current_prices:
                current_price = current_prices[symbol_lower.replace("-", "")].get("price", 0)
            else:
                # Fallback: utiliser le prix moyen si pas de prix actuel
                current_price = avg_price
            
            current_value = amount * current_price
            cost_basis = amount * avg_price
            pnl = current_value - cost_basis
            pnl_percent = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
            
            total_holdings_value += current_value
            total_cost_basis += cost_basis
            
            positions.append({
                "symbol": symbol,
                "amount": amount,
                "avg_price": avg_price,
                "current_price": current_price,
                "current_value": current_value,
                "cost_basis": cost_basis,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "entry_date": entry_date
            })
        
        total_value = balance + total_holdings_value
        total_pnl = total_value - 10000.0
        total_pnl_percent = (total_pnl / 10000.0) * 100
        
        logger.info(f"Portfolio for user {current_user['id']}: {len(positions)} positions, value: ${total_value:.2f}")
        
        return {
            "balance": balance,
            "portfolio": portfolio,
            "positions": positions,
            "initial_balance": 10000.0,
            "total_value": total_value,
            "total_holdings_value": total_holdings_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return {
            "balance": 10000.0,
            "portfolio": {},
            "positions": [],
            "initial_balance": 10000.0,
            "total_value": 10000.0,
            "total_pnl": 0,
            "total_pnl_percent": 0
        }

@router.post("/reset")
async def reset_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Reset paper trading portfolio"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"paper_balance": 10000.0, "portfolio": {}}}
    )
    await db.paper_trades.delete_many({"user_id": current_user["id"]})
    return {"message": "Portfolio reset successfully", "balance": 10000.0}
