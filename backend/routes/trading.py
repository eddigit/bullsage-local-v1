"""
Trading Routes - Technical analysis, signals, and AI recommendations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import httpx

from core.config import db, logger, EMERGENT_LLM_KEY, CRYPTOCOMPARE_API_URL, ALPHA_VANTAGE_API_KEY
from core.auth import get_current_user
from services.market_data import market_data_service, CRYPTO_MAPPING, SMART_INVEST_STOCKS
from services.technical_analysis import technical_analysis_service

router = APIRouter(prefix="/trading", tags=["trading"])


class TradingAnalysisRequest(BaseModel):
    coin_id: str
    timeframe: str = "4h"  # 1h, 4h, daily
    trading_style: str = "swing"  # scalping, intraday, swing


class SmartInvestRequest(BaseModel):
    investment_amount: float
    include_stocks: bool = True


class SmartInvestExecute(BaseModel):
    coin_id: str
    asset_type: str = "crypto"
    amount_usd: float
    entry_price: float


@router.post("/analyze")
async def analyze_for_trading(request: TradingAnalysisRequest, current_user: dict = Depends(get_current_user)):
    """Deep technical analysis for trading decisions"""
    coin_id = request.coin_id
    timeframe = request.timeframe
    
    # Map timeframe to days
    days_map = {"1h": 1, "4h": 7, "daily": 30}
    days = days_map.get(timeframe, 7)
    
    # Get historical prices
    prices = await market_data_service.get_historical_prices(coin_id, days)
    
    if not prices or len(prices) < 10:
        raise HTTPException(
            status_code=503,
            detail="Impossible de récupérer les données historiques. Réessayez dans 30 secondes."
        )
    
    current_price = prices[-1]
    
    # Generate trading signal
    signal = technical_analysis_service.generate_trading_signal(prices, current_price)
    
    return {
        "coin_id": coin_id,
        "timeframe": timeframe,
        "current_price": current_price,
        "indicators": signal["indicators"],
        "recommendation": {
            "action": signal["action"],
            "confidence": signal["confidence"],
            "message": signal["message"],
            "score": signal["score"],
            "reasons": signal["reasons"],
            "risk_factors": [],
            "levels": signal["levels"],
            "risk_reward_ratio": 1.0
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/smart-invest/analyze")
async def smart_invest_analyze(request: SmartInvestRequest, current_user: dict = Depends(get_current_user)):
    """Analyze the market and recommend the best investment opportunity"""
    if request.investment_amount < 10:
        return {"error": "Montant minimum: 10€"}
    
    watchlist = current_user.get("watchlist", ["bitcoin", "ethereum", "solana", "ripple", "cardano"])
    if not watchlist:
        watchlist = ["bitcoin", "ethereum", "solana"]
    
    best_opportunity = None
    best_score = -999
    all_opportunities = []
    
    try:
        # Get current prices
        symbols = []
        for coin_id in watchlist[:10]:
            if coin_id in CRYPTO_MAPPING:
                symbols.append(CRYPTO_MAPPING[coin_id]["binance_symbol"])
        
        if not symbols:
            symbols = ["BTC", "ETH", "SOL", "XRP", "ADA"]
        
        price_data = await market_data_service.get_crypto_prices(
            [k for k in CRYPTO_MAPPING.keys() if CRYPTO_MAPPING[k]["binance_symbol"] in symbols]
        )
        
        if not price_data:
            return {"error": "Impossible de récupérer les prix. Réessayez dans 30 secondes."}
        
        # Analyze each coin
        for coin_id in watchlist[:8]:
            if coin_id not in CRYPTO_MAPPING:
                continue
            
            coin_info = CRYPTO_MAPPING[coin_id]
            crypto_symbol = coin_info["binance_symbol"]
            
            # Get price from CryptoCompare data
            if crypto_symbol not in price_data or "USD" not in price_data[crypto_symbol]:
                continue
            
            usd_data = price_data[crypto_symbol]["USD"]
            current_price = usd_data.get("PRICE", 0)
            change_24h = usd_data.get("CHANGEPCT24HOUR", 0)
            
            if current_price <= 0:
                continue
            
            # Get historical data
            prices = await market_data_service.get_historical_prices(coin_id, 7)
            if not prices or len(prices) < 30:
                continue
            
            # Generate signal
            signal = technical_analysis_service.generate_trading_signal(prices, current_price)
            score = signal["score"]
            
            if score >= 2:
                quantity = request.investment_amount / current_price
                
                opportunity = {
                    "coin_id": coin_id,
                    "name": coin_info["name"],
                    "symbol": crypto_symbol,
                    "asset_type": "crypto",
                    "current_price": current_price,
                    "change_24h": change_24h,
                    "score": round(score, 1),
                    "confidence": "HAUTE" if score >= 5 else "MOYENNE" if score >= 3 else "MODÉRÉE",
                    "quantity_to_buy": quantity,
                    "investment_amount": request.investment_amount,
                    "indicators": {
                        "rsi": signal["indicators"]["rsi"],
                        "trend": signal["indicators"].get("moving_averages", {}).get("trend", "neutral"),
                        "bollinger": signal["indicators"]["bollinger"]["position"],
                        "macd": signal["indicators"]["macd"]["trend"]
                    },
                    "levels": signal["levels"],
                    "reasons": signal["reasons"],
                    "source": "cryptocompare"
                }
                
                all_opportunities.append(opportunity)
                
                if score > best_score:
                    best_score = score
                    best_opportunity = opportunity
        
        # Analyze stocks if enabled
        if request.include_stocks and ALPHA_VANTAGE_API_KEY:
            for stock_info in SMART_INVEST_STOCKS[:3]:
                stock_data = await market_data_service.get_stock_data(stock_info["symbol"])
                if not stock_data:
                    continue
                
                time_series = stock_data.get("Time Series (Daily)", {})
                dates = sorted(time_series.keys(), reverse=True)[:30]
                
                if len(dates) < 14:
                    continue
                
                prices = [float(time_series[d]["4. close"]) for d in reversed(dates)]
                current_price = prices[-1]
                
                signal = technical_analysis_service.generate_trading_signal(prices, current_price)
                score = signal["score"]
                
                if score >= 2:
                    quantity = request.investment_amount / current_price
                    
                    stock_opportunity = {
                        "coin_id": stock_info["symbol"],
                        "name": stock_info["name"],
                        "symbol": stock_info["symbol"],
                        "asset_type": "stock",
                        "stock_type": stock_info["type"],
                        "current_price": current_price,
                        "change_24h": 0,
                        "score": round(score, 1),
                        "confidence": "HAUTE" if score >= 5 else "MOYENNE" if score >= 3 else "MODÉRÉE",
                        "quantity_to_buy": quantity,
                        "investment_amount": request.investment_amount,
                        "indicators": {
                            "rsi": signal["indicators"]["rsi"],
                            "trend": signal["indicators"].get("moving_averages", {}).get("trend", "neutral"),
                            "bollinger": signal["indicators"]["bollinger"]["position"],
                            "macd": signal["indicators"]["macd"]["trend"]
                        },
                        "levels": signal["levels"],
                        "reasons": signal["reasons"],
                        "source": "alphavantage"
                    }
                    
                    all_opportunities.append(stock_opportunity)
                    
                    if score > best_score:
                        best_score = score
                        best_opportunity = stock_opportunity
        
        if not best_opportunity:
            return {
                "error": "Aucune opportunité détectée. Les marchés sont neutres ou en surachat.",
                "message": "BULL recommande d'attendre une meilleure opportunité."
            }
        
        # Add other opportunities
        best_opportunity["other_opportunities"] = [
            {"name": o["name"], "symbol": o["symbol"], "score": o["score"], "asset_type": o.get("asset_type", "crypto")}
            for o in sorted(all_opportunities, key=lambda x: x["score"], reverse=True)[:5]
            if o["coin_id"] != best_opportunity["coin_id"]
        ]
        
        return best_opportunity
        
    except Exception as e:
        logger.error(f"Smart Invest analysis error: {e}")
        return {"error": f"Erreur lors de l'analyse: {str(e)}"}


@router.post("/smart-invest/execute")
async def smart_invest_execute(request: SmartInvestExecute, current_user: dict = Depends(get_current_user)):
    """Execute a Smart Invest trade in paper trading"""
    user_id = current_user["id"]
    
    # Get user's paper trading balance
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    paper_balance = user.get("paper_balance", 10000)
    
    if request.amount_usd > paper_balance:
        return {"error": "Solde insuffisant en Paper Trading"}
    
    # Calculate quantity
    quantity = request.amount_usd / request.entry_price
    
    # Create trade record
    trade = {
        "id": f"smart_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "user_id": user_id,
        "coin_id": request.coin_id,
        "asset_type": request.asset_type,
        "type": "buy",
        "source": "smart_invest",
        "quantity": quantity,
        "entry_price": request.entry_price,
        "amount_usd": request.amount_usd,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.paper_trades.insert_one(trade)
    
    # Update portfolio
    portfolio = user.get("portfolio", [])
    existing = next((p for p in portfolio if p["coin_id"] == request.coin_id), None)
    
    if existing:
        total_quantity = existing["quantity"] + quantity
        total_cost = (existing["quantity"] * existing["avg_price"]) + request.amount_usd
        existing["quantity"] = total_quantity
        existing["avg_price"] = total_cost / total_quantity
    else:
        portfolio.append({
            "coin_id": request.coin_id,
            "symbol": request.coin_id.upper()[:4],
            "quantity": quantity,
            "avg_price": request.entry_price
        })
    
    # Update balance
    new_balance = paper_balance - request.amount_usd
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"paper_balance": new_balance, "portfolio": portfolio}}
    )
    
    return {
        "success": True,
        "message": f"✅ Investissement de ${request.amount_usd:.2f} en {request.coin_id} effectué!",
        "trade_id": trade["id"],
        "quantity": quantity,
        "entry_price": request.entry_price,
        "total_invested": request.amount_usd,
        "new_balance": new_balance
    }


@router.get("/briefing")
async def get_morning_briefing(current_user: dict = Depends(get_current_user)):
    """Get AI-generated morning market briefing"""
    try:
        # Get market data
        crypto_list = await market_data_service.get_crypto_list()
        
        if not crypto_list:
            return {"error": "Impossible de récupérer les données de marché"}
        
        # Get top movers
        top_gainers = sorted(
            [c for c in crypto_list if c.get("price_change_percentage_24h")],
            key=lambda x: x.get("price_change_percentage_24h", 0),
            reverse=True
        )[:3]
        
        top_losers = sorted(
            [c for c in crypto_list if c.get("price_change_percentage_24h")],
            key=lambda x: x.get("price_change_percentage_24h", 0)
        )[:3]
        
        # Get Fear & Greed
        fear_greed = None
        try:
            async with httpx.AsyncClient() as client:
                fg_response = await client.get(
                    "https://api.alternative.me/fng/",
                    params={"limit": 1},
                    timeout=10.0
                )
                if fg_response.status_code == 200:
                    fg_data = fg_response.json()
                    if fg_data.get("data"):
                        fear_greed = fg_data["data"][0]
        except Exception:
            pass
        
        # Generate briefing
        btc = next((c for c in crypto_list if c["id"] == "bitcoin"), None)
        eth = next((c for c in crypto_list if c["id"] == "ethereum"), None)
        
        briefing = {
            "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            "market_overview": {
                "bitcoin": {
                    "price": btc["current_price"] if btc else 0,
                    "change_24h": btc.get("price_change_percentage_24h", 0) if btc else 0
                },
                "ethereum": {
                    "price": eth["current_price"] if eth else 0,
                    "change_24h": eth.get("price_change_percentage_24h", 0) if eth else 0
                }
            },
            "sentiment": {
                "fear_greed": fear_greed,
                "market_trend": "bullish" if (btc and btc.get("price_change_percentage_24h", 0) > 0) else "bearish"
            },
            "top_movers": {
                "gainers": [
                    {"name": c["name"], "symbol": c["symbol"], "change": c.get("price_change_percentage_24h", 0)}
                    for c in top_gainers
                ],
                "losers": [
                    {"name": c["name"], "symbol": c["symbol"], "change": c.get("price_change_percentage_24h", 0)}
                    for c in top_losers
                ]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return briefing
        
    except Exception as e:
        logger.error(f"Morning briefing error: {e}")
        return {"error": "Erreur lors de la génération du briefing"}


@router.get("/scan-opportunities")
async def scan_trading_opportunities(current_user: dict = Depends(get_current_user)):
    """Scan watchlist for trading opportunities"""
    watchlist = current_user.get("watchlist", ["bitcoin", "ethereum", "solana"])
    opportunities = []
    
    for coin_id in watchlist[:10]:
        try:
            prices = await market_data_service.get_historical_prices(coin_id, 7)
            if not prices or len(prices) < 30:
                continue
            
            current_price = prices[-1]
            signal = technical_analysis_service.generate_trading_signal(prices, current_price)
            
            if signal["score"] >= 2 or signal["score"] <= -2:
                coin_name = coin_id.replace("-", " ").title()
                if coin_id in CRYPTO_MAPPING:
                    coin_name = CRYPTO_MAPPING[coin_id]["name"]
                
                opportunities.append({
                    "coin_id": coin_id,
                    "name": coin_name,
                    "action": signal["action"],
                    "score": signal["score"],
                    "confidence": signal["confidence"],
                    "current_price": current_price,
                    "reasons": signal["reasons"][:2]
                })
        except Exception as e:
            logger.warning(f"Error scanning {coin_id}: {e}")
            continue
    
    # Sort by absolute score
    opportunities.sort(key=lambda x: abs(x["score"]), reverse=True)
    
    return {"opportunities": opportunities, "scanned": len(watchlist)}
