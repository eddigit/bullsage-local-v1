"""
Market Routes - Crypto, Forex, and Market Intelligence endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import httpx
from datetime import datetime, timezone

from core.config import (
    db, logger,
    COINGECKO_API_URL, CRYPTOCOMPARE_API_URL,
    ALPHA_VANTAGE_API_KEY, FINNHUB_API_KEY, FRED_API_KEY, MARKETAUX_API_KEY
)
from core.auth import get_current_user
from services.market_data import market_data_service, CRYPTO_MAPPING

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/crypto")
async def get_crypto_markets(current_user: dict = Depends(get_current_user)):
    """Get top cryptocurrencies with current prices"""
    data = await market_data_service.get_crypto_list()
    
    if data:
        return data
    
    raise HTTPException(
        status_code=503,
        detail="Les APIs de données crypto sont temporairement indisponibles. Veuillez réessayer dans quelques minutes."
    )


@router.get("/crypto/{coin_id}")
async def get_crypto_detail(coin_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed info for a specific cryptocurrency"""
    try:
        async with httpx.AsyncClient() as client:
            # Try CryptoCompare first
            if coin_id in CRYPTO_MAPPING:
                symbol = CRYPTO_MAPPING[coin_id]["binance_symbol"]
                response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/pricemultifull",
                    params={"fsyms": symbol, "tsyms": "USD"},
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "RAW" in data and symbol in data["RAW"]:
                        usd_data = data["RAW"][symbol]["USD"]
                        return {
                            "id": coin_id,
                            "symbol": symbol.lower(),
                            "name": CRYPTO_MAPPING[coin_id]["name"],
                            "image": {"large": CRYPTO_MAPPING[coin_id]["image"]},
                            "market_data": {
                                "current_price": {"usd": usd_data.get("PRICE", 0)},
                                "market_cap": {"usd": usd_data.get("MKTCAP", 0)},
                                "total_volume": {"usd": usd_data.get("TOTALVOLUME24HTO", 0)},
                                "high_24h": {"usd": usd_data.get("HIGH24HOUR", 0)},
                                "low_24h": {"usd": usd_data.get("LOW24HOUR", 0)},
                                "price_change_percentage_24h": usd_data.get("CHANGEPCT24HOUR", 0),
                                "circulating_supply": usd_data.get("CIRCULATINGSUPPLY", 0)
                            },
                            "source": "cryptocompare"
                        }
            
            # Fallback to CoinGecko
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                raise HTTPException(status_code=503, detail="API rate limited. Réessayez dans 1 minute.")
            else:
                raise HTTPException(status_code=404, detail="Crypto not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching crypto detail: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données")


@router.get("/crypto/{coin_id}/history")
async def get_crypto_history(
    coin_id: str,
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get historical price data for a cryptocurrency"""
    prices = await market_data_service.get_historical_prices(coin_id, days)
    
    if prices:
        return {"prices": prices, "coin_id": coin_id, "days": days}
    
    raise HTTPException(status_code=503, detail="Impossible de récupérer l'historique des prix")


@router.get("/fear-greed")
async def get_fear_greed_index(current_user: dict = Depends(get_current_user)):
    """Get Crypto Fear & Greed Index"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.alternative.me/fng/",
                params={"limit": 7},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            
            return []
    except Exception as e:
        logger.error(f"Fear & Greed API error: {e}")
        return []


@router.get("/intelligence")
async def get_market_intelligence(current_user: dict = Depends(get_current_user)):
    """Get comprehensive market intelligence (macro data)"""
    intelligence = {
        "fear_greed": None,
        "btc_dominance": None,
        "market_cap_total": None,
        "volume_24h": None,
        "economic_indicators": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Fear & Greed
            try:
                fg_response = await client.get(
                    "https://api.alternative.me/fng/",
                    params={"limit": 1},
                    timeout=10.0
                )
                if fg_response.status_code == 200:
                    fg_data = fg_response.json()
                    if fg_data.get("data"):
                        intelligence["fear_greed"] = fg_data["data"][0]
            except Exception as e:
                logger.warning(f"Fear & Greed fetch error: {e}")
            
            # CoinGecko Global Data
            try:
                global_response = await client.get(
                    f"{COINGECKO_API_URL}/global",
                    timeout=15.0
                )
                if global_response.status_code == 200:
                    global_data = global_response.json().get("data", {})
                    intelligence["btc_dominance"] = global_data.get("market_cap_percentage", {}).get("btc")
                    intelligence["market_cap_total"] = global_data.get("total_market_cap", {}).get("usd")
                    intelligence["volume_24h"] = global_data.get("total_volume", {}).get("usd")
            except Exception as e:
                logger.warning(f"CoinGecko global fetch error: {e}")
            
            # FRED Economic Data
            if FRED_API_KEY:
                fred_indicators = {
                    "DFF": "fed_funds_rate",
                    "CPIAUCSL": "cpi",
                    "UNRATE": "unemployment"
                }
                
                for series_id, name in fred_indicators.items():
                    try:
                        fred_response = await client.get(
                            "https://api.stlouisfed.org/fred/series/observations",
                            params={
                                "series_id": series_id,
                                "api_key": FRED_API_KEY,
                                "file_type": "json",
                                "sort_order": "desc",
                                "limit": 1
                            },
                            timeout=10.0
                        )
                        if fred_response.status_code == 200:
                            fred_data = fred_response.json()
                            observations = fred_data.get("observations", [])
                            if observations:
                                intelligence["economic_indicators"][name] = {
                                    "value": observations[0].get("value"),
                                    "date": observations[0].get("date")
                                }
                    except Exception as e:
                        logger.warning(f"FRED {series_id} fetch error: {e}")
            
            return intelligence
            
    except Exception as e:
        logger.error(f"Market intelligence error: {e}")
        return intelligence


@router.get("/news")
async def get_market_news(
    category: str = "crypto",
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get market news from various sources"""
    news = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Finnhub News
            if FINNHUB_API_KEY:
                try:
                    finnhub_response = await client.get(
                        "https://finnhub.io/api/v1/news",
                        params={
                            "category": "crypto" if category == "crypto" else "general",
                            "token": FINNHUB_API_KEY
                        },
                        timeout=10.0
                    )
                    if finnhub_response.status_code == 200:
                        finnhub_news = finnhub_response.json()[:limit]
                        for item in finnhub_news:
                            news.append({
                                "title": item.get("headline", ""),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", ""),
                                "source": item.get("source", "Finnhub"),
                                "published_at": datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc).isoformat(),
                                "image": item.get("image", "")
                            })
                except Exception as e:
                    logger.warning(f"Finnhub news error: {e}")
            
            # Marketaux News
            if MARKETAUX_API_KEY and len(news) < limit:
                try:
                    marketaux_response = await client.get(
                        "https://api.marketaux.com/v1/news/all",
                        params={
                            "api_token": MARKETAUX_API_KEY,
                            "filter_entities": "true",
                            "language": "en",
                            "limit": limit - len(news)
                        },
                        timeout=10.0
                    )
                    if marketaux_response.status_code == 200:
                        marketaux_news = marketaux_response.json().get("data", [])
                        for item in marketaux_news:
                            news.append({
                                "title": item.get("title", ""),
                                "summary": item.get("description", ""),
                                "url": item.get("url", ""),
                                "source": item.get("source", "Marketaux"),
                                "published_at": item.get("published_at", ""),
                                "image": item.get("image_url", "")
                            })
                except Exception as e:
                    logger.warning(f"Marketaux news error: {e}")
            
            return news[:limit]
            
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return []


@router.get("/forex")
async def get_forex_rates(current_user: dict = Depends(get_current_user)):
    """Get major forex rates"""
    if not ALPHA_VANTAGE_API_KEY:
        return {"error": "Alpha Vantage API key not configured"}
    
    forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"]
    rates = []
    
    try:
        async with httpx.AsyncClient() as client:
            for pair in forex_pairs:
                from_currency = pair[:3]
                to_currency = pair[3:]
                
                response = await client.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "apikey": ALPHA_VANTAGE_API_KEY
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rate_data = data.get("Realtime Currency Exchange Rate", {})
                    if rate_data:
                        rates.append({
                            "pair": pair,
                            "from": from_currency,
                            "to": to_currency,
                            "rate": float(rate_data.get("5. Exchange Rate", 0)),
                            "bid": float(rate_data.get("8. Bid Price", 0)),
                            "ask": float(rate_data.get("9. Ask Price", 0)),
                            "timestamp": rate_data.get("6. Last Refreshed", "")
                        })
        
        return rates
        
    except Exception as e:
        logger.error(f"Forex fetch error: {e}")
        return []
