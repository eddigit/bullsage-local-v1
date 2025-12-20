from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import numpy as np
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'bullsage_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
COINGECKO_API_URL = os.environ.get('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
FRED_API_KEY = os.environ.get('FRED_API_KEY')
MARKETAUX_API_KEY = os.environ.get('MARKETAUX_API_KEY')

# Create the main app
app = FastAPI(title="BULL SAGE API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    trading_level: str = "beginner"  # beginner, intermediate, advanced

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    trading_level: str
    created_at: str
    paper_balance: float = 10000.0
    watchlist: List[str] = []
    is_admin: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ChatMessage(BaseModel):
    role: str  # user or assistant
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class PaperTrade(BaseModel):
    id: str
    user_id: str
    symbol: str
    type: str  # buy or sell
    amount: float
    price: float
    timestamp: str
    status: str = "executed"

class PaperTradeCreate(BaseModel):
    symbol: str
    type: str  # buy or sell
    amount: float
    price: float

class AlertCreate(BaseModel):
    symbol: str
    target_price: float
    condition: str  # above or below
    name: Optional[str] = None

class AlertResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    target_price: float
    condition: str
    name: str
    active: bool
    created_at: str

class StrategyCreate(BaseModel):
    name: str
    description: str
    indicators: List[str]
    entry_rules: str
    exit_rules: str
    risk_percentage: float = 2.0

class TradingSignal(BaseModel):
    id: str
    user_id: str
    symbol: str
    symbol_name: str
    signal_type: str  # BUY, SELL, WAIT
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    timeframe: str
    confidence: str  # low, medium, high
    reason: str
    price_at_signal: float
    created_at: str
    status: str = "active"  # active, hit_tp1, hit_tp2, hit_sl, expired
    result_pnl: Optional[float] = None

class SignalCreate(BaseModel):
    symbol: str
    symbol_name: str
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    timeframe: str
    confidence: str
    reason: str
    price_at_signal: float


class StrategyResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    indicators: List[str]
    entry_rules: str
    exit_rules: str
    risk_percentage: float
    created_at: str

class WatchlistUpdate(BaseModel):
    symbols: List[str]

# ============== AUTH HELPERS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "trading_level": user_data.trading_level,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_balance": 10000.0,
        "watchlist": ["bitcoin", "ethereum", "solana"],
        "portfolio": {}
    }
    
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user_data.email)
    
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        trading_level=user_data.trading_level,
        created_at=user_doc["created_at"],
        paper_balance=user_doc["paper_balance"],
        watchlist=user_doc["watchlist"],
        is_admin=False
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"])
    
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        trading_level=user.get("trading_level", "beginner"),
        created_at=user["created_at"],
        paper_balance=user.get("paper_balance", 10000.0),
        watchlist=user.get("watchlist", []),
        is_admin=user.get("is_admin", False)
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        trading_level=current_user.get("trading_level", "beginner"),
        created_at=current_user["created_at"],
        paper_balance=current_user.get("paper_balance", 10000.0),
        watchlist=current_user.get("watchlist", []),
        is_admin=current_user.get("is_admin", False)
    )

# ============== MARKET DATA ROUTES ==============

# Simple in-memory cache for crypto data
_crypto_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 60  # Cache for 60 seconds
}

# Fallback crypto data when API is rate limited
FALLBACK_CRYPTO_DATA = [
    {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 1, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "ethereum", "symbol": "eth", "name": "Ethereum", "image": "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 2, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "tether", "symbol": "usdt", "name": "Tether", "image": "https://coin-images.coingecko.com/coins/images/325/large/Tether.png", "current_price": 1, "market_cap": 0, "market_cap_rank": 3, "price_change_percentage_24h": 0, "high_24h": 1, "low_24h": 1, "sparkline_in_7d": {"price": []}},
    {"id": "binancecoin", "symbol": "bnb", "name": "BNB", "image": "https://coin-images.coingecko.com/coins/images/825/large/bnb-icon2_2x.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 4, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "solana", "symbol": "sol", "name": "Solana", "image": "https://coin-images.coingecko.com/coins/images/4128/large/solana.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 5, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "ripple", "symbol": "xrp", "name": "XRP", "image": "https://coin-images.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 6, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "usd-coin", "symbol": "usdc", "name": "USDC", "image": "https://coin-images.coingecko.com/coins/images/6319/large/usdc.png", "current_price": 1, "market_cap": 0, "market_cap_rank": 7, "price_change_percentage_24h": 0, "high_24h": 1, "low_24h": 1, "sparkline_in_7d": {"price": []}},
    {"id": "cardano", "symbol": "ada", "name": "Cardano", "image": "https://coin-images.coingecko.com/coins/images/975/large/cardano.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 8, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "dogecoin", "symbol": "doge", "name": "Dogecoin", "image": "https://coin-images.coingecko.com/coins/images/5/large/dogecoin.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 9, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "avalanche-2", "symbol": "avax", "name": "Avalanche", "image": "https://coin-images.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 10, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "polkadot", "symbol": "dot", "name": "Polkadot", "image": "https://coin-images.coingecko.com/coins/images/12171/large/polkadot.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 11, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "chainlink", "symbol": "link", "name": "Chainlink", "image": "https://coin-images.coingecko.com/coins/images/877/large/chainlink-new-logo.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 12, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "polygon", "symbol": "matic", "name": "Polygon", "image": "https://coin-images.coingecko.com/coins/images/4713/large/polygon.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 13, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "litecoin", "symbol": "ltc", "name": "Litecoin", "image": "https://coin-images.coingecko.com/coins/images/2/large/litecoin.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 14, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
    {"id": "shiba-inu", "symbol": "shib", "name": "Shiba Inu", "image": "https://coin-images.coingecko.com/coins/images/11939/large/shiba.png", "current_price": 0, "market_cap": 0, "market_cap_rank": 15, "price_change_percentage_24h": 0, "high_24h": 0, "low_24h": 0, "sparkline_in_7d": {"price": []}},
]

async def fetch_crypto_with_simple_api():
    """Fetch basic price data using CoinGecko simple/price endpoint (less rate limited)"""
    coin_ids = ",".join([c["id"] for c in FALLBACK_CRYPTO_DATA])
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={
                    "ids": coin_ids,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true"
                },
                timeout=15.0
            )
            if response.status_code == 200:
                prices = response.json()
                # Update fallback data with real prices
                updated_data = []
                for coin in FALLBACK_CRYPTO_DATA:
                    coin_data = coin.copy()
                    if coin["id"] in prices:
                        coin_data["current_price"] = prices[coin["id"]].get("usd", 0)
                        coin_data["price_change_percentage_24h"] = prices[coin["id"]].get("usd_24h_change", 0)
                    updated_data.append(coin_data)
                return updated_data
    except Exception as e:
        logger.error(f"Simple price API error: {e}")
    return None

@api_router.get("/market/crypto")
async def get_crypto_markets(current_user: dict = Depends(get_current_user)):
    """Get top cryptocurrencies from CoinGecko with caching and fallback"""
    global _crypto_cache
    
    # Check cache first
    now = datetime.now(timezone.utc)
    if _crypto_cache["data"] and _crypto_cache["timestamp"]:
        age = (now - _crypto_cache["timestamp"]).total_seconds()
        if age < _crypto_cache["ttl"]:
            logger.info("Returning cached crypto data")
            return _crypto_cache["data"]
    
    # Try main API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 50,
                    "page": 1,
                    "sparkline": True,
                    "price_change_percentage": "24h,7d"
                },
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                # Update cache
                _crypto_cache["data"] = data
                _crypto_cache["timestamp"] = now
                return data
            elif response.status_code == 429:
                logger.warning("CoinGecko rate limited, trying simple API...")
                # Try simple price API as fallback
                simple_data = await fetch_crypto_with_simple_api()
                if simple_data:
                    _crypto_cache["data"] = simple_data
                    _crypto_cache["timestamp"] = now
                    return simple_data
                # Return cached or fallback
                if _crypto_cache["data"]:
                    logger.info("Returning stale cached data due to rate limit")
                    return _crypto_cache["data"]
                logger.warning("Returning fallback crypto data")
                return FALLBACK_CRYPTO_DATA
            else:
                logger.error(f"CoinGecko API error: {response.status_code}")
                return _crypto_cache["data"] if _crypto_cache["data"] else FALLBACK_CRYPTO_DATA
    except Exception as e:
        logger.error(f"Error fetching crypto markets: {e}")
        return _crypto_cache["data"] if _crypto_cache["data"] else FALLBACK_CRYPTO_DATA

@api_router.get("/market/crypto/{coin_id}")
async def get_crypto_detail(coin_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed info for a specific cryptocurrency"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}",
                params={
                    "localization": False,
                    "tickers": False,
                    "market_data": True,
                    "community_data": False,
                    "developer_data": False
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=404, detail="Coin not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching coin detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch coin data")

@api_router.get("/market/crypto/{coin_id}/chart")
async def get_crypto_chart(coin_id: str, days: int = 7, current_user: dict = Depends(get_current_user)):
    """Get historical price data for charts"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": days
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"CoinGecko chart API returned {response.status_code}")
                # Return empty but valid structure
                return {"prices": [], "market_caps": [], "total_volumes": []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        return {"prices": [], "market_caps": [], "total_volumes": []}

@api_router.get("/market/trending")
async def get_trending(current_user: dict = Depends(get_current_user)):
    """Get trending cryptocurrencies"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{COINGECKO_API_URL}/search/trending", timeout=30.0)
            if response.status_code == 200:
                return response.json()
            return {"coins": []}
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        return {"coins": []}

# ============== FEAR & GREED INDEX (NO API KEY REQUIRED) ==============

@api_router.get("/market/fear-greed")
async def get_fear_greed(current_user: dict = Depends(get_current_user)):
    """Get Crypto Fear & Greed Index from Alternative.me"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.alternative.me/fng/",
                params={"limit": 30},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {"data": []}
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed: {e}")
        return {"data": []}

# ============== FINNHUB ROUTES (NEWS, SENTIMENT, CALENDAR) ==============

# Cache for AI news summary
_news_summary_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 1800  # 30 minutes cache
}

@api_router.get("/market/news-impact")
async def get_news_impact_summary(current_user: dict = Depends(get_current_user)):
    """
    Get AI-summarized news impact in French.
    Returns concise market-moving news with bullish/bearish indicators.
    """
    global _news_summary_cache
    
    # Check cache
    now = datetime.now(timezone.utc)
    if _news_summary_cache["data"] and _news_summary_cache["timestamp"]:
        age = (now - _news_summary_cache["timestamp"]).total_seconds()
        if age < _news_summary_cache["ttl"]:
            return _news_summary_cache["data"]
    
    # Fetch recent news
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/news",
                params={"category": "crypto", "token": FINNHUB_API_KEY},
                timeout=30.0
            )
            news_items = response.json()[:10] if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error fetching news for summary: {e}")
        news_items = []
    
    if not news_items:
        return {
            "summary": [],
            "last_updated": now.isoformat(),
            "source": "Finnhub"
        }
    
    # Prepare news for AI analysis
    news_text = "\n".join([
        f"- {item.get('headline', '')} (Source: {item.get('source', 'Unknown')})"
        for item in news_items[:8]
    ])
    
    # Use AI to summarize and translate
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"news_summary_{datetime.now().strftime('%Y%m%d%H')}",
            system_message="""Tu es un analyste financier expert. Ta tâche est de résumer les actualités crypto importantes en français.

Pour chaque news importante, donne:
1. Un résumé TRÈS CONCIS (1 ligne max)
2. L'impact sur le marché: HAUSSIER 📈, BAISSIER 📉, ou NEUTRE ➡️
3. Ce que le trader devrait faire

Format de réponse STRICT (JSON array):
[
  {"news": "Résumé concis en français", "impact": "HAUSSIER", "action": "Opportunité d'achat"},
  {"news": "Autre news", "impact": "BAISSIER", "action": "Prudence recommandée"}
]

Maximum 4-5 news les plus importantes. Sois TRÈS concis."""
        )
        chat.with_model("openai", "gpt-4o")
        
        ai_response = await asyncio.to_thread(chat.send_message, f"Analyse ces actualités crypto des dernières 48h et résume en français avec impact marché:\n\n{news_text}")
        
        # Parse AI response
        response_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            import json
            summary_data = json.loads(json_match.group())
        else:
            # Fallback: create simple summary
            summary_data = [{"news": "Actualités en cours d'analyse", "impact": "NEUTRE", "action": "Surveiller le marché"}]
        
        result = {
            "summary": summary_data[:5],  # Max 5 items
            "last_updated": now.isoformat(),
            "source": "Finnhub + AI Analysis"
        }
        
        # Update cache
        _news_summary_cache["data"] = result
        _news_summary_cache["timestamp"] = now
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating news summary: {e}")
        # Return raw headlines as fallback
        fallback = [
            {"news": item.get("headline", "")[:80], "impact": "NEUTRE", "action": "À analyser"}
            for item in news_items[:3]
        ]
        return {
            "summary": fallback,
            "last_updated": now.isoformat(),
            "source": "Finnhub (raw)"
        }

@api_router.get("/market/news")
async def get_market_news(category: str = "general", current_user: dict = Depends(get_current_user)):
    """Get market news from Finnhub"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/news",
                params={"category": category, "token": FINNHUB_API_KEY},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()[:20]  # Limit to 20 news
            return []
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []

@api_router.get("/market/news/{symbol}")
async def get_symbol_news(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get news for a specific symbol from Finnhub"""
    try:
        today = datetime.now(timezone.utc)
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": symbol.upper(),
                    "from": from_date,
                    "to": to_date,
                    "token": FINNHUB_API_KEY
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()[:15]
            return []
    except Exception as e:
        logger.error(f"Error fetching symbol news: {e}")
        return []

@api_router.get("/market/sentiment/{symbol}")
async def get_sentiment(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get sentiment data for a symbol from Finnhub"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/news-sentiment",
                params={"symbol": symbol.upper(), "token": FINNHUB_API_KEY},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        return {}

@api_router.get("/market/economic-calendar")
async def get_economic_calendar(current_user: dict = Depends(get_current_user)):
    """Get economic calendar events from Finnhub"""
    try:
        today = datetime.now(timezone.utc)
        from_date = today.strftime("%Y-%m-%d")
        to_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/calendar/economic",
                params={"from": from_date, "to": to_date, "token": FINNHUB_API_KEY},
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("economicCalendar", [])[:30]
            return []
    except Exception as e:
        logger.error(f"Error fetching economic calendar: {e}")
        return []

# ============== ALPHA VANTAGE ROUTES (FOREX, STOCKS, INDICATORS) ==============

@api_router.get("/market/forex/{from_currency}/{to_currency}")
async def get_forex_rate(from_currency: str, to_currency: str, current_user: dict = Depends(get_current_user)):
    """Get real-time forex exchange rate from Alpha Vantage"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper(),
                    "apikey": ALPHA_VANTAGE_API_KEY
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error fetching forex rate: {e}")
        return {}

@api_router.get("/market/forex-daily/{from_symbol}/{to_symbol}")
async def get_forex_daily(from_symbol: str, to_symbol: str, current_user: dict = Depends(get_current_user)):
    """Get daily forex data from Alpha Vantage"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "FX_DAILY",
                    "from_symbol": from_symbol.upper(),
                    "to_symbol": to_symbol.upper(),
                    "apikey": ALPHA_VANTAGE_API_KEY
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error fetching forex daily: {e}")
        return {}

@api_router.get("/market/stock/{symbol}")
async def get_stock_quote(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get stock quote from Alpha Vantage"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol.upper(),
                    "apikey": ALPHA_VANTAGE_API_KEY
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error fetching stock quote: {e}")
        return {}

@api_router.get("/market/indicators/{symbol}/{indicator}")
async def get_technical_indicator(symbol: str, indicator: str, interval: str = "daily", current_user: dict = Depends(get_current_user)):
    """Get technical indicators (RSI, MACD, etc.) from Alpha Vantage"""
    try:
        params = {
            "function": indicator.upper(),
            "symbol": symbol.upper(),
            "interval": interval,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        # Add specific params for each indicator
        if indicator.upper() == "RSI":
            params["time_period"] = 14
            params["series_type"] = "close"
        elif indicator.upper() == "MACD":
            params["series_type"] = "close"
        elif indicator.upper() in ["SMA", "EMA"]:
            params["time_period"] = 20
            params["series_type"] = "close"
        elif indicator.upper() == "BBANDS":
            params["time_period"] = 20
            params["series_type"] = "close"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.alphavantage.co/query",
                params=params,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error fetching indicator: {e}")
        return {}

# ============== FRED ROUTES (ECONOMIC DATA) ==============

@api_router.get("/market/fred/{series_id}")
async def get_fred_data(series_id: str, current_user: dict = Depends(get_current_user)):
    """Get economic data from FRED (Federal Reserve)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id.upper(),
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 30
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {"observations": []}
    except Exception as e:
        logger.error(f"Error fetching FRED data: {e}")
        return {"observations": []}

@api_router.get("/market/macro-overview")
async def get_macro_overview(current_user: dict = Depends(get_current_user)):
    """Get key macro economic indicators"""
    try:
        series_ids = {
            "fed_rate": "FEDFUNDS",
            "inflation": "CPIAUCSL", 
            "unemployment": "UNRATE",
            "gdp": "GDP",
            "vix": "VIXCLS"
        }
        
        results = {}
        async with httpx.AsyncClient() as client:
            for key, series_id in series_ids.items():
                try:
                    response = await client.get(
                        "https://api.stlouisfed.org/fred/series/observations",
                        params={
                            "series_id": series_id,
                            "api_key": FRED_API_KEY,
                            "file_type": "json",
                            "sort_order": "desc",
                            "limit": 1
                        },
                        timeout=15.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("observations"):
                            results[key] = {
                                "value": data["observations"][0].get("value"),
                                "date": data["observations"][0].get("date"),
                                "series_id": series_id
                            }
                except Exception as e:
                    logger.error(f"Error fetching {series_id}: {e}")
                    continue
        
        return results
    except Exception as e:
        logger.error(f"Error fetching macro overview: {e}")
        return {}

# ============== MARKETAUX ROUTES (NEWS SENTIMENT) ==============

@api_router.get("/market/news-sentiment")
async def get_news_sentiment(symbols: str = "BTCUSD,ETHUSD", current_user: dict = Depends(get_current_user)):
    """Get news with sentiment analysis from Marketaux"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.marketaux.com/v1/news/all",
                params={
                    "symbols": symbols,
                    "filter_entities": "true",
                    "language": "en",
                    "api_token": MARKETAUX_API_KEY
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {"data": []}
    except Exception as e:
        logger.error(f"Error fetching news sentiment: {e}")
        return {"data": []}

# ============== TRADING SIGNALS ROUTES ==============

@api_router.post("/signals", response_model=TradingSignal)
async def create_signal(signal: SignalCreate, current_user: dict = Depends(get_current_user)):
    """Create a new trading signal"""
    signal_id = str(uuid.uuid4())
    signal_doc = {
        "id": signal_id,
        "user_id": current_user["id"],
        "symbol": signal.symbol,
        "symbol_name": signal.symbol_name,
        "signal_type": signal.signal_type,
        "entry_price": signal.entry_price,
        "stop_loss": signal.stop_loss,
        "take_profit_1": signal.take_profit_1,
        "take_profit_2": signal.take_profit_2,
        "timeframe": signal.timeframe,
        "confidence": signal.confidence,
        "reason": signal.reason,
        "price_at_signal": signal.price_at_signal,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "result_pnl": None
    }
    await db.signals.insert_one(signal_doc)
    return TradingSignal(**signal_doc)

@api_router.get("/signals")
async def get_signals(limit: int = 50, status: str = None, current_user: dict = Depends(get_current_user)):
    """Get user's trading signals"""
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return signals

@api_router.get("/signals/stats")
async def get_signal_stats(current_user: dict = Depends(get_current_user)):
    """Get trading signal statistics"""
    signals = await db.signals.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    
    total = len(signals)
    if total == 0:
        return {
            "total_signals": 0,
            "active": 0,
            "hit_tp1": 0,
            "hit_tp2": 0,
            "hit_sl": 0,
            "expired": 0,
            "win_rate": 0,
            "by_symbol": {},
            "by_timeframe": {}
        }
    
    active = len([s for s in signals if s["status"] == "active"])
    hit_tp1 = len([s for s in signals if s["status"] == "hit_tp1"])
    hit_tp2 = len([s for s in signals if s["status"] == "hit_tp2"])
    hit_sl = len([s for s in signals if s["status"] == "hit_sl"])
    expired = len([s for s in signals if s["status"] == "expired"])
    
    completed = hit_tp1 + hit_tp2 + hit_sl
    wins = hit_tp1 + hit_tp2
    win_rate = (wins / completed * 100) if completed > 0 else 0
    
    # Stats by symbol
    by_symbol = {}
    for s in signals:
        sym = s["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = {"total": 0, "wins": 0}
        by_symbol[sym]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_symbol[sym]["wins"] += 1
    
    # Stats by timeframe
    by_timeframe = {}
    for s in signals:
        tf = s["timeframe"]
        if tf not in by_timeframe:
            by_timeframe[tf] = {"total": 0, "wins": 0}
        by_timeframe[tf]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_timeframe[tf]["wins"] += 1
    
    return {
        "total_signals": total,
        "active": active,
        "hit_tp1": hit_tp1,
        "hit_tp2": hit_tp2,
        "hit_sl": hit_sl,
        "expired": expired,
        "win_rate": round(win_rate, 1),
        "by_symbol": by_symbol,
        "by_timeframe": by_timeframe
    }

@api_router.put("/signals/{signal_id}/status")
async def update_signal_status(signal_id: str, status: str, result_pnl: float = None, current_user: dict = Depends(get_current_user)):
    """Update signal status (hit_tp1, hit_tp2, hit_sl, expired)"""
    valid_statuses = ["active", "hit_tp1", "hit_tp2", "hit_sl", "expired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {"status": status}
    if result_pnl is not None:
        update_data["result_pnl"] = result_pnl
    
    result = await db.signals.update_one(
        {"id": signal_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return {"message": "Signal updated", "status": status}

@api_router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a signal"""
    result = await db.signals.delete_one({"id": signal_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted"}

@api_router.post("/signals/evaluate")
async def evaluate_signals(current_user: dict = Depends(get_current_user)):
    """
    Automatically evaluate active signals against current market prices.
    Checks if TP1, TP2, or SL have been hit and updates status/PnL accordingly.
    """
    # Get all active signals for this user
    active_signals = await db.signals.find(
        {"user_id": current_user["id"], "status": "active"},
        {"_id": 0}
    ).to_list(100)
    
    if not active_signals:
        return {"message": "No active signals to evaluate", "updated": 0, "results": []}
    
    # Get unique symbols
    symbols = list(set([s["symbol"] for s in active_signals]))
    symbols_str = ",".join(symbols)
    
    # Fetch current prices from CoinGecko
    current_prices = {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={"ids": symbols_str, "vs_currencies": "usd"},
                timeout=15.0
            )
            if response.status_code == 200:
                price_data = response.json()
                for symbol, data in price_data.items():
                    current_prices[symbol] = data.get("usd", 0)
        except Exception as e:
            logger.error(f"Error fetching prices for evaluation: {e}")
            raise HTTPException(status_code=500, detail="Could not fetch current prices")
    
    results = []
    updated_count = 0
    
    for signal in active_signals:
        symbol = signal["symbol"]
        current_price = current_prices.get(symbol)
        
        if not current_price:
            results.append({
                "signal_id": signal["id"],
                "symbol": symbol,
                "status": "error",
                "message": "Could not fetch current price"
            })
            continue
        
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        tp1 = signal["take_profit_1"]
        tp2 = signal.get("take_profit_2")
        signal_type = signal["signal_type"]
        
        new_status = None
        pnl_percent = 0
        
        # Calculate based on signal type (BUY or SELL)
        if signal_type == "BUY":
            # For BUY signals: price going up is good
            if current_price <= stop_loss:
                new_status = "hit_sl"
                pnl_percent = ((stop_loss - entry_price) / entry_price) * 100
            elif tp2 and current_price >= tp2:
                new_status = "hit_tp2"
                pnl_percent = ((tp2 - entry_price) / entry_price) * 100
            elif current_price >= tp1:
                new_status = "hit_tp1"
                pnl_percent = ((tp1 - entry_price) / entry_price) * 100
        elif signal_type == "SELL":
            # For SELL signals: price going down is good
            if current_price >= stop_loss:
                new_status = "hit_sl"
                pnl_percent = ((entry_price - stop_loss) / entry_price) * 100
            elif tp2 and current_price <= tp2:
                new_status = "hit_tp2"
                pnl_percent = ((entry_price - tp2) / entry_price) * 100
            elif current_price <= tp1:
                new_status = "hit_tp1"
                pnl_percent = ((entry_price - tp1) / entry_price) * 100
        
        # Check for expiration (signals older than 7 days for daily, 1 day for 1h/4h)
        created_at = datetime.fromisoformat(signal["created_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600
        
        if signal["timeframe"] == "daily" and age_hours > 168:  # 7 days
            if not new_status:
                new_status = "expired"
                pnl_percent = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
        elif signal["timeframe"] in ["1h", "4h"] and age_hours > 24:  # 1 day
            if not new_status:
                new_status = "expired"
                pnl_percent = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
        
        if new_status:
            # Update the signal in database
            await db.signals.update_one(
                {"id": signal["id"]},
                {"$set": {
                    "status": new_status,
                    "result_pnl": round(pnl_percent, 2),
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "price_at_evaluation": current_price
                }}
            )
            updated_count += 1
            results.append({
                "signal_id": signal["id"],
                "symbol": signal["symbol_name"],
                "signal_type": signal_type,
                "old_status": "active",
                "new_status": new_status,
                "entry_price": entry_price,
                "current_price": current_price,
                "pnl_percent": round(pnl_percent, 2)
            })
        else:
            # Signal still active
            unrealized_pnl = ((current_price - entry_price) / entry_price) * 100 if signal_type == "BUY" else ((entry_price - current_price) / entry_price) * 100
            results.append({
                "signal_id": signal["id"],
                "symbol": signal["symbol_name"],
                "signal_type": signal_type,
                "status": "active",
                "entry_price": entry_price,
                "current_price": current_price,
                "unrealized_pnl": round(unrealized_pnl, 2),
                "tp1_distance": round(((tp1 - current_price) / current_price) * 100, 2) if signal_type == "BUY" else round(((current_price - tp1) / current_price) * 100, 2),
                "sl_distance": round(((current_price - stop_loss) / current_price) * 100, 2) if signal_type == "BUY" else round(((stop_loss - current_price) / current_price) * 100, 2)
            })
    
    return {
        "message": f"Evaluated {len(active_signals)} signals, updated {updated_count}",
        "total_evaluated": len(active_signals),
        "updated": updated_count,
        "results": results
    }

# ============== TRADING EXPERT SYSTEM ==============

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return 50.0  # Neutral if not enough data
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_macd(prices: List[float]) -> Dict[str, float]:
    """Calculate MACD (Moving Average Convergence Divergence)"""
    if len(prices) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    prices_arr = np.array(prices)
    
    # EMA 12
    ema12 = prices_arr[-12:].mean()  # Simplified EMA
    # EMA 26
    ema26 = prices_arr[-26:].mean()
    
    macd_line = ema12 - ema26
    signal_line = macd_line * 0.9  # Simplified signal
    histogram = macd_line - signal_line
    
    return {
        "macd": round(macd_line, 4),
        "signal": round(signal_line, 4),
        "histogram": round(histogram, 4),
        "trend": "bullish" if histogram > 0 else "bearish"
    }

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        current = prices[-1] if prices else 0
        return {"upper": current * 1.02, "middle": current, "lower": current * 0.98, "position": "middle"}
    
    prices_arr = np.array(prices[-period:])
    middle = np.mean(prices_arr)
    std = np.std(prices_arr)
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    current = prices[-1]
    
    # Determine position
    if current >= upper:
        position = "overbought"
    elif current <= lower:
        position = "oversold"
    elif current > middle:
        position = "upper_half"
    else:
        position = "lower_half"
    
    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "current": round(current, 2),
        "position": position
    }

def calculate_moving_averages(prices: List[float]) -> Dict[str, Any]:
    """Calculate Moving Averages (MA 20, 50, 200)"""
    result = {}
    current = prices[-1] if prices else 0
    
    if len(prices) >= 20:
        result["ma20"] = round(np.mean(prices[-20:]), 2)
    else:
        result["ma20"] = current
        
    if len(prices) >= 50:
        result["ma50"] = round(np.mean(prices[-50:]), 2)
    else:
        result["ma50"] = current
        
    if len(prices) >= 200:
        result["ma200"] = round(np.mean(prices[-200:]), 2)
    else:
        result["ma200"] = current
    
    # Trend analysis
    if result["ma20"] > result["ma50"] > result["ma200"]:
        result["trend"] = "strong_bullish"
    elif result["ma20"] > result["ma50"]:
        result["trend"] = "bullish"
    elif result["ma20"] < result["ma50"] < result["ma200"]:
        result["trend"] = "strong_bearish"
    elif result["ma20"] < result["ma50"]:
        result["trend"] = "bearish"
    else:
        result["trend"] = "neutral"
    
    return result

def calculate_support_resistance(prices: List[float]) -> Dict[str, float]:
    """Calculate Support and Resistance levels"""
    if len(prices) < 10:
        current = prices[-1] if prices else 0
        return {"support": current * 0.95, "resistance": current * 1.05}
    
    prices_arr = np.array(prices)
    
    # Simple support/resistance based on recent highs/lows
    recent = prices_arr[-50:] if len(prices_arr) >= 50 else prices_arr
    
    support = float(np.percentile(recent, 10))
    resistance = float(np.percentile(recent, 90))
    
    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "current": round(prices[-1], 2)
    }

def analyze_candlestick_patterns(prices: List[float]) -> Dict[str, Any]:
    """Analyze candlestick patterns (simplified)"""
    if len(prices) < 5:
        return {"pattern": "insufficient_data", "signal": "neutral"}
    
    recent = prices[-5:]
    
    # Simplified pattern detection
    if recent[-1] > recent[-2] > recent[-3]:
        pattern = "three_white_soldiers"
        signal = "bullish"
    elif recent[-1] < recent[-2] < recent[-3]:
        pattern = "three_black_crows"
        signal = "bearish"
    elif abs(recent[-1] - recent[-2]) < (recent[-1] * 0.001):
        pattern = "doji"
        signal = "reversal_possible"
    elif recent[-1] > recent[-2] and recent[-2] < recent[-3]:
        pattern = "hammer"
        signal = "bullish_reversal"
    elif recent[-1] < recent[-2] and recent[-2] > recent[-3]:
        pattern = "shooting_star"
        signal = "bearish_reversal"
    else:
        pattern = "none"
        signal = "neutral"
    
    return {"pattern": pattern, "signal": signal}

def generate_trading_recommendation(indicators: Dict) -> Dict[str, Any]:
    """Generate trading recommendation based on all indicators"""
    score = 0
    reasons = []
    
    # RSI Analysis
    rsi = indicators.get("rsi", 50)
    if rsi < 30:
        score += 2
        reasons.append(f"RSI en survente ({rsi}) - Signal d'achat")
    elif rsi < 40:
        score += 1
        reasons.append(f"RSI bas ({rsi}) - Potentiel de rebond")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI en surachat ({rsi}) - Signal de vente")
    elif rsi > 60:
        score -= 1
        reasons.append(f"RSI élevé ({rsi}) - Prudence")
    
    # MACD Analysis
    macd = indicators.get("macd", {})
    if macd.get("trend") == "bullish":
        score += 1
        reasons.append("MACD haussier - Momentum positif")
    elif macd.get("trend") == "bearish":
        score -= 1
        reasons.append("MACD baissier - Momentum négatif")
    
    # Bollinger Analysis
    bb = indicators.get("bollinger", {})
    if bb.get("position") == "oversold":
        score += 2
        reasons.append("Prix sur bande inférieure Bollinger - Survente")
    elif bb.get("position") == "overbought":
        score -= 2
        reasons.append("Prix sur bande supérieure Bollinger - Surachat")
    
    # MA Trend
    ma = indicators.get("moving_averages", {})
    trend = ma.get("trend", "neutral")
    if trend == "strong_bullish":
        score += 2
        reasons.append("Tendance fortement haussière (MA20 > MA50 > MA200)")
    elif trend == "bullish":
        score += 1
        reasons.append("Tendance haussière")
    elif trend == "strong_bearish":
        score -= 2
        reasons.append("Tendance fortement baissière (MA20 < MA50 < MA200)")
    elif trend == "bearish":
        score -= 1
        reasons.append("Tendance baissière")
    
    # Candlestick patterns
    candles = indicators.get("candlesticks", {})
    if candles.get("signal") == "bullish" or candles.get("signal") == "bullish_reversal":
        score += 1
        reasons.append(f"Pattern chandelier: {candles.get('pattern')} - Haussier")
    elif candles.get("signal") == "bearish" or candles.get("signal") == "bearish_reversal":
        score -= 1
        reasons.append(f"Pattern chandelier: {candles.get('pattern')} - Baissier")
    
    # Generate recommendation
    if score >= 4:
        action = "STRONG_BUY"
        confidence = "high"
        message = "🟢 ACHAT FORT recommandé"
    elif score >= 2:
        action = "BUY"
        confidence = "medium"
        message = "🟢 ACHAT recommandé"
    elif score <= -4:
        action = "STRONG_SELL"
        confidence = "high"
        message = "🔴 VENTE FORTE recommandée"
    elif score <= -2:
        action = "SELL"
        confidence = "medium"
        message = "🔴 VENTE recommandée"
    else:
        action = "WAIT"
        confidence = "low"
        message = "🟡 ATTENDRE - Pas de signal clair"
    
    return {
        "action": action,
        "confidence": confidence,
        "message": message,
        "score": score,
        "reasons": reasons
    }

class TradingAnalysisRequest(BaseModel):
    coin_id: str
    timeframe: str = "4h"  # 1h, 4h, daily
    trading_style: str = "swing"  # scalping, intraday, swing

@api_router.post("/trading/analyze")
async def analyze_for_trading(request: TradingAnalysisRequest, current_user: dict = Depends(get_current_user)):
    """
    Deep technical analysis for trading decisions.
    Returns indicators + AI recommendation.
    """
    coin_id = request.coin_id
    timeframe = request.timeframe
    trading_style = request.trading_style
    
    # Map timeframe to days of data needed
    days_map = {"1h": 1, "4h": 7, "daily": 30}
    days = days_map.get(timeframe, 7)
    
    # Fetch historical price data
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                params={"vs_currency": "usd", "days": days},
                timeout=30.0
            )
            
            if response.status_code != 200:
                # Try cache or return error
                raise HTTPException(status_code=503, detail="Unable to fetch market data")
            
            data = response.json()
            prices = [p[1] for p in data.get("prices", [])]
            volumes = [v[1] for v in data.get("total_volumes", [])]
            
            if not prices:
                raise HTTPException(status_code=404, detail="No price data available")
            
            # Get current market info
            market_response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}",
                params={"localization": False, "tickers": False, "community_data": False, "developer_data": False},
                timeout=15.0
            )
            
            market_data = {}
            if market_response.status_code == 200:
                coin_data = market_response.json()
                market_data = coin_data.get("market_data", {})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching data for trading analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
    
    # Calculate all indicators
    indicators = {
        "rsi": calculate_rsi(prices),
        "macd": calculate_macd(prices),
        "bollinger": calculate_bollinger_bands(prices),
        "moving_averages": calculate_moving_averages(prices),
        "support_resistance": calculate_support_resistance(prices),
        "candlesticks": analyze_candlestick_patterns(prices)
    }
    
    # Generate algorithmic recommendation
    algo_recommendation = generate_trading_recommendation(indicators)
    
    # Current price info
    current_price = prices[-1]
    price_24h_change = market_data.get("price_change_percentage_24h", 0)
    high_24h = market_data.get("high_24h", {}).get("usd", current_price * 1.01)
    low_24h = market_data.get("low_24h", {}).get("usd", current_price * 0.99)
    
    # Calculate entry, SL, TP based on indicators
    sr = indicators["support_resistance"]
    bb = indicators["bollinger"]
    
    if algo_recommendation["action"] in ["BUY", "STRONG_BUY"]:
        entry_price = current_price
        stop_loss = max(sr["support"], bb["lower"]) * 0.99
        take_profit_1 = min(sr["resistance"], bb["upper"]) * 0.95
        take_profit_2 = sr["resistance"] * 1.02
    elif algo_recommendation["action"] in ["SELL", "STRONG_SELL"]:
        entry_price = current_price
        stop_loss = min(sr["resistance"], bb["upper"]) * 1.01
        take_profit_1 = max(sr["support"], bb["lower"]) * 1.05
        take_profit_2 = sr["support"] * 0.98
    else:
        entry_price = current_price
        stop_loss = sr["support"] * 0.99
        take_profit_1 = sr["resistance"] * 0.98
        take_profit_2 = sr["resistance"] * 1.02
    
    # Build context for AI
    ai_context = f"""
ANALYSE TECHNIQUE COMPLÈTE - {coin_id.upper()}
Timeframe: {timeframe} | Style: {trading_style}

PRIX ACTUEL: ${current_price:,.2f}
Variation 24h: {price_24h_change:.2f}%
High 24h: ${high_24h:,.2f} | Low 24h: ${low_24h:,.2f}

INDICATEURS TECHNIQUES:
- RSI (14): {indicators['rsi']} {'(SURVENTE)' if indicators['rsi'] < 30 else '(SURACHAT)' if indicators['rsi'] > 70 else ''}
- MACD: {indicators['macd']['macd']:.4f} | Signal: {indicators['macd']['signal']:.4f} | Tendance: {indicators['macd']['trend']}
- Bollinger: Upper ${bb['upper']:,.2f} | Middle ${bb['middle']:,.2f} | Lower ${bb['lower']:,.2f}
- Position Bollinger: {bb['position']}
- MA20: ${indicators['moving_averages']['ma20']:,.2f} | MA50: ${indicators['moving_averages']['ma50']:,.2f}
- Tendance MA: {indicators['moving_averages']['trend']}
- Support: ${sr['support']:,.2f} | Résistance: ${sr['resistance']:,.2f}
- Pattern Chandelier: {indicators['candlesticks']['pattern']} ({indicators['candlesticks']['signal']})

RECOMMANDATION ALGORITHMIQUE: {algo_recommendation['action']}
Score: {algo_recommendation['score']}/10
Raisons: {'; '.join(algo_recommendation['reasons'])}

NIVEAUX SUGGÉRÉS:
- Entrée: ${entry_price:,.2f}
- Stop-Loss: ${stop_loss:,.2f} ({((entry_price - stop_loss) / entry_price * 100):.1f}%)
- TP1: ${take_profit_1:,.2f} ({((take_profit_1 - entry_price) / entry_price * 100):.1f}%)
- TP2: ${take_profit_2:,.2f} ({((take_profit_2 - entry_price) / entry_price * 100):.1f}%)

En tant que trader expert, donne ton analyse et ta recommandation finale.
Sois direct et précis. Indique clairement: ACHETER, VENDRE ou ATTENDRE.
Explique pourquoi en 3-4 points clés maximum.
"""

    # Get AI analysis
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"trading_analysis_{current_user['id']}_{datetime.now().strftime('%Y%m%d%H%M')}",
            system_message=f"""Tu es BULL, un trader professionnel expert avec 20 ans d'expérience.
Tu analyses les marchés crypto avec précision et donnes des conseils actionnables.
Style de trading demandé: {trading_style}
Timeframe: {timeframe}
Niveau du trader: {current_user.get('trading_level', 'intermediate')}

Tu dois être DIRECT et CLAIR. Pas de blabla. Des décisions concrètes.
Utilise les indicateurs fournis pour justifier ta recommandation."""
        )
        chat.with_model("openai", "gpt-4o")
        
        ai_response = await chat.send_message_async(ai_context)
        ai_analysis = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        ai_analysis = f"Analyse algorithmique: {algo_recommendation['message']}\n\nRaisons:\n" + "\n".join([f"• {r}" for r in algo_recommendation['reasons']])
    
    # Check if this is an alert-worthy situation
    is_alert = algo_recommendation["action"] in ["STRONG_BUY", "STRONG_SELL", "BUY", "SELL"]
    
    return {
        "coin_id": coin_id,
        "timeframe": timeframe,
        "trading_style": trading_style,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_price": current_price,
        "price_change_24h": price_24h_change,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "indicators": indicators,
        "recommendation": algo_recommendation,
        "levels": {
            "entry": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit_1": round(take_profit_1, 2),
            "take_profit_2": round(take_profit_2, 2)
        },
        "ai_analysis": ai_analysis,
        "is_alert": is_alert
    }

@api_router.get("/trading/scan-opportunities")
async def scan_trading_opportunities(current_user: dict = Depends(get_current_user)):
    """
    Scan watchlist for trading opportunities.
    Returns alerts for coins with strong signals.
    """
    watchlist = current_user.get("watchlist", [])
    
    if not watchlist:
        return {"alerts": [], "message": "Watchlist vide"}
    
    alerts = []
    
    for coin_id in watchlist[:10]:  # Limit to 10 to avoid rate limits
        try:
            # Quick analysis
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": 7},
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                prices = [p[1] for p in data.get("prices", [])]
                
                if not prices:
                    continue
                
                # Quick indicator check
                rsi = calculate_rsi(prices)
                bb = calculate_bollinger_bands(prices)
                
                # Check for alert conditions
                alert_type = None
                if rsi < 30 and bb["position"] == "oversold":
                    alert_type = "STRONG_BUY"
                elif rsi < 35:
                    alert_type = "BUY"
                elif rsi > 70 and bb["position"] == "overbought":
                    alert_type = "STRONG_SELL"
                elif rsi > 65:
                    alert_type = "SELL"
                
                if alert_type:
                    alerts.append({
                        "coin_id": coin_id,
                        "alert_type": alert_type,
                        "rsi": rsi,
                        "current_price": prices[-1],
                        "bollinger_position": bb["position"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            logger.error(f"Error scanning {coin_id}: {e}")
            continue
    
    return {
        "alerts": alerts,
        "scanned": len(watchlist),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============== MARKET INTELLIGENCE ENDPOINT ==============

@api_router.get("/market/intelligence")
async def get_market_intelligence(current_user: dict = Depends(get_current_user)):
    """Get comprehensive market intelligence dashboard data"""
    data = await fetch_comprehensive_market_data()
    analysis = analyze_market_conditions(data)
    
    return {
        "timestamp": data["timestamp"],
        "crypto_prices": data["crypto"],
        "fear_greed": {
            "current": data["fear_greed"],
            "history": data["fear_greed_history"]
        },
        "macro": data["macro"],
        "economic_calendar": data["economic_calendar"],
        "news": data["news"][:10],
        "analysis": analysis
    }

# ============== AI ASSISTANT ROUTES ==============

async def fetch_comprehensive_market_data(coin_ids: str = "bitcoin,ethereum,solana,cardano,ripple"):
    """Fetch ALL available market data for AI context"""
    data = {
        "crypto": [],
        "fear_greed": None,
        "fear_greed_history": [],
        "news": [],
        "news_sentiment": {},
        "macro": {},
        "economic_calendar": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Crypto prices from CoinGecko (with more data)
        try:
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": coin_ids,
                    "order": "market_cap_desc",
                    "sparkline": True,
                    "price_change_percentage": "1h,24h,7d,30d"
                },
                timeout=15.0
            )
            if response.status_code == 200:
                data["crypto"] = response.json()
        except Exception as e:
            logger.error(f"Error fetching crypto: {e}")

        # 2. Fear & Greed Index (current + history)
        try:
            response = await client.get(
                "https://api.alternative.me/fng/",
                params={"limit": 7},
                timeout=10.0
            )
            if response.status_code == 200:
                fng = response.json()
                if fng.get("data"):
                    data["fear_greed"] = fng["data"][0]
                    data["fear_greed_history"] = fng["data"]
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")

        # 3. Market News from Finnhub (crypto focus)
        try:
            response = await client.get(
                "https://finnhub.io/api/v1/news",
                params={"category": "crypto", "token": FINNHUB_API_KEY},
                timeout=15.0
            )
            if response.status_code == 200:
                news = response.json()
                data["news"] = news[:10] if news else []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

        # 4. Economic Calendar (next 7 days important events)
        try:
            today = datetime.now(timezone.utc)
            from_date = today.strftime("%Y-%m-%d")
            to_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            
            response = await client.get(
                "https://finnhub.io/api/v1/calendar/economic",
                params={"from": from_date, "to": to_date, "token": FINNHUB_API_KEY},
                timeout=15.0
            )
            if response.status_code == 200:
                cal = response.json()
                # Filter for important events (US focus)
                important_events = [e for e in cal.get("economicCalendar", []) 
                                   if e.get("country") == "US" and e.get("impact") in ["high", "medium"]]
                data["economic_calendar"] = important_events[:10]
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")

        # 5. Macro data from FRED
        macro_series = {
            "vix": "VIXCLS",
            "fed_rate": "FEDFUNDS",
            "dxy": "DTWEXBGS",  # Dollar Index
        }
        
        for key, series_id in macro_series.items():
            try:
                response = await client.get(
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
                if response.status_code == 200:
                    fred_data = response.json()
                    if fred_data.get("observations"):
                        data["macro"][key] = {
                            "value": fred_data["observations"][0].get("value"),
                            "date": fred_data["observations"][0].get("date")
                        }
            except Exception as e:
                logger.error(f"Error fetching {series_id}: {e}")

    return data

def analyze_market_conditions(data: dict) -> dict:
    """Analyze market conditions and generate insights"""
    analysis = {
        "overall_sentiment": "neutral",
        "risk_level": "medium",
        "key_factors": [],
        "opportunities": [],
        "warnings": []
    }
    
    # Fear & Greed analysis
    if data.get("fear_greed"):
        fg_value = int(data["fear_greed"].get("value", 50))
        if fg_value <= 20:
            analysis["overall_sentiment"] = "extreme_fear"
            analysis["key_factors"].append(f"Fear & Greed à {fg_value} = EXTREME FEAR - Opportunité d'achat potentielle")
            analysis["opportunities"].append("Marché en panique - historiquement bon timing pour accumuler")
        elif fg_value <= 40:
            analysis["overall_sentiment"] = "fear"
            analysis["key_factors"].append(f"Fear & Greed à {fg_value} = FEAR - Prudence mais opportunités possibles")
        elif fg_value >= 80:
            analysis["overall_sentiment"] = "extreme_greed"
            analysis["key_factors"].append(f"Fear & Greed à {fg_value} = EXTREME GREED - Risque de correction élevé")
            analysis["warnings"].append("Marché euphorique - risque de correction majeure")
        elif fg_value >= 60:
            analysis["overall_sentiment"] = "greed"
            analysis["key_factors"].append(f"Fear & Greed à {fg_value} = GREED - Vigilance sur les prises de profit")
    
    # VIX analysis
    if data.get("macro", {}).get("vix"):
        try:
            vix = float(data["macro"]["vix"]["value"])
            if vix < 15:
                analysis["key_factors"].append(f"VIX à {vix:.1f} = Faible volatilité - Marché calme")
                analysis["risk_level"] = "low"
            elif vix > 25:
                analysis["key_factors"].append(f"VIX à {vix:.1f} = Haute volatilité - ATTENTION")
                analysis["risk_level"] = "high"
                analysis["warnings"].append("VIX élevé = incertitude sur les marchés")
            else:
                analysis["key_factors"].append(f"VIX à {vix:.1f} = Volatilité normale")
        except:
            pass
    
    # Economic events
    if data.get("economic_calendar"):
        high_impact = [e for e in data["economic_calendar"] if e.get("impact") == "high"]
        if high_impact:
            events_str = ", ".join([e.get("event", "")[:30] for e in high_impact[:3]])
            analysis["warnings"].append(f"Événements économiques importants à venir: {events_str}")
    
    return analysis

@api_router.post("/assistant/chat", response_model=ChatResponse)
async def chat_with_bull(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat with BULL SAGE AI Assistant - with real-time market data"""
    try:
        # Get user's trading level for personalized responses
        trading_level = current_user.get("trading_level", "beginner")
        user_name = current_user.get("name", "Trader")
        
        # FETCH ALL REAL-TIME DATA
        market_data = await fetch_comprehensive_market_data()
        
        # Analyze market conditions
        market_analysis = analyze_market_conditions(market_data)
        
        # Build comprehensive market context
        market_context = f"""
=== DONNÉES MARCHÉ TEMPS RÉEL ({market_data['timestamp'][:19].replace('T', ' ')} UTC) ===

📊 PRIX CRYPTO ACTUELS:"""
        
        for coin in market_data["crypto"]:
            price = coin.get("current_price", 0)
            change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
            change_24h = coin.get("price_change_percentage_24h", 0) or 0
            change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
            change_30d = coin.get("price_change_percentage_30d_in_currency", 0) or 0
            high_24h = coin.get("high_24h", 0)
            low_24h = coin.get("low_24h", 0)
            ath = coin.get("ath", 0)
            ath_change = coin.get("ath_change_percentage", 0) or 0
            market_context += f"""
- {coin['name']} ({coin['symbol'].upper()}): ${price:,.2f}
  • 1h: {change_1h:+.2f}% | 24h: {change_24h:+.2f}% | 7j: {change_7d:+.2f}% | 30j: {change_30d:+.2f}%
  • High 24h: ${high_24h:,.2f} | Low 24h: ${low_24h:,.2f}
  • ATH: ${ath:,.2f} ({ath_change:+.1f}% du ATH)"""

        # Fear & Greed Index
        if market_data["fear_greed"]:
            fg = market_data["fear_greed"]
            market_context += f"""

😱 FEAR & GREED INDEX: {fg.get('value', 'N/A')} ({fg.get('value_classification', 'N/A')})
  • Interprétation: """
            fg_value = int(fg.get('value', 50))
            if fg_value <= 25:
                market_context += "EXTREME FEAR - Signal potentiel d'ACHAT (marché sous-évalué)"
            elif fg_value <= 45:
                market_context += "FEAR - Prudence, possible opportunité d'achat"
            elif fg_value <= 55:
                market_context += "NEUTRAL - Marché indécis"
            elif fg_value <= 75:
                market_context += "GREED - Prudence, risque de correction"
            else:
                market_context += "EXTREME GREED - Signal de VENTE potentiel (marché suracheté)"

        # Macro data
        if market_data["macro"]:
            market_context += f"""

🏦 DONNÉES MACRO:"""
            if market_data["macro"].get("vix"):
                vix_val = market_data["macro"]["vix"].get("value", "N/A")
                market_context += f"""
- VIX (Volatilité): {vix_val}"""
                try:
                    vix_num = float(vix_val)
                    if vix_num < 15:
                        market_context += " (Faible - marché calme, bon pour prendre des positions)"
                    elif vix_num < 25:
                        market_context += " (Normal)"
                    else:
                        market_context += " (ÉLEVÉ - PRUDENCE, forte incertitude)"
                except:
                    pass
            
            if market_data["macro"].get("fed_rate"):
                market_context += f"""
- Taux Fed: {market_data["macro"]["fed_rate"].get("value", "N/A")}%"""
            
            if market_data["macro"].get("dxy"):
                market_context += f"""
- Dollar Index (DXY): {market_data["macro"]["dxy"].get("value", "N/A")} (Dollar fort = crypto faible généralement)"""

        # Fear & Greed History (trend)
        if market_data.get("fear_greed_history") and len(market_data["fear_greed_history"]) > 1:
            current_fg = int(market_data["fear_greed_history"][0].get("value", 50))
            week_ago_fg = int(market_data["fear_greed_history"][-1].get("value", 50))
            fg_change = current_fg - week_ago_fg
            market_context += f"""
- Fear & Greed Tendance 7j: {week_ago_fg} → {current_fg} ({fg_change:+d} points)"""

        # Economic Calendar
        if market_data.get("economic_calendar"):
            market_context += """

📅 CALENDRIER ÉCONOMIQUE (événements importants à venir):"""
            for event in market_data["economic_calendar"][:5]:
                event_name = event.get("event", "")[:50]
                event_date = event.get("date", "")
                impact = event.get("impact", "").upper()
                market_context += f"""
- [{impact}] {event_date}: {event_name}"""

        # News headlines
        if market_data["news"]:
            market_context += """

📰 DERNIÈRES NEWS CRYPTO:"""
            for news in market_data["news"][:5]:
                headline = news.get("headline", "")[:80]
                source = news.get("source", "")
                market_context += f"""
- {headline} ({source})"""

        # AI-generated analysis summary
        market_context += f"""

🤖 ANALYSE AUTOMATIQUE DU MARCHÉ:
- Sentiment global: {market_analysis['overall_sentiment'].upper()}
- Niveau de risque: {market_analysis['risk_level'].upper()}"""
        
        if market_analysis["key_factors"]:
            market_context += """
- Facteurs clés:"""
            for factor in market_analysis["key_factors"]:
                market_context += f"""
  • {factor}"""
        
        if market_analysis["warnings"]:
            market_context += """
- ⚠️ ALERTES:"""
            for warning in market_analysis["warnings"]:
                market_context += f"""
  • {warning}"""
        
        if market_analysis["opportunities"]:
            market_context += """
- 💡 OPPORTUNITÉS:"""
            for opp in market_analysis["opportunities"]:
                market_context += f"""
  • {opp}"""

        market_context += """

=== FIN DES DONNÉES TEMPS RÉEL ==="""

        system_message = f"""Tu es BULL SAGE, un assistant de trading IA PROFESSIONNEL. Tu accompagnes {user_name}, un trader de niveau {trading_level}.

🎯 TON OBJECTIF PRINCIPAL: Donner des conseils de trading PRÉCIS et ACTIONNABLES basés sur les données TEMPS RÉEL ci-dessous.

{market_context}

📋 FORMAT DE RÉPONSE OBLIGATOIRE pour les demandes d'analyse/trading:

1. **SITUATION ACTUELLE** (prix, tendance, sentiment)
2. **ANALYSE TECHNIQUE** (supports, résistances, indicateurs clés)
3. **RECOMMANDATION CLAIRE**:
   - 🟢 ACHAT ou 🔴 VENTE ou 🟡 ATTENDRE
   - Point d'entrée précis
   - Stop-Loss (SL)
   - Take-Profit 1 (TP1) et Take-Profit 2 (TP2)
   - Risque/Récompense ratio
4. **TIMING** (immédiat, attendre pullback, etc.)
5. **GESTION DU RISQUE** (% du capital recommandé)

⚠️ RÈGLES CRITIQUES:
- TOUJOURS utiliser les données temps réel fournies ci-dessus
- JAMAIS dire que tu n'as pas accès aux prix - TU AS TOUS LES PRIX
- Donner des niveaux de prix PRÉCIS (pas de fourchettes vagues)
- Adapter la complexité au niveau {trading_level}
- Rappeler que le trading comporte des risques
- Ne jamais risquer plus de 1-2% par trade

🗣️ Réponds TOUJOURS en français, de manière directe et actionnable."""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"bullsage_{current_user['id']}_{datetime.now().strftime('%Y%m%d%H')}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.1")
        
        user_message = UserMessage(text=request.message)
        response = await chat.send_message(user_message)
        
        # Store chat history
        chat_doc = {
            "user_id": current_user["id"],
            "message": request.message,
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_data_snapshot": {
                "btc_price": market_data["crypto"][0].get("current_price") if market_data["crypto"] else None,
                "fear_greed": market_data["fear_greed"].get("value") if market_data["fear_greed"] else None
            }
        }
        await db.chat_history.insert_one(chat_doc)
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"AI Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")

@api_router.get("/assistant/history")
async def get_chat_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get chat history for current user"""
    history = await db.chat_history.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    return list(reversed(history))

# ============== PAPER TRADING ROUTES ==============

@api_router.post("/paper-trading/trade", response_model=PaperTrade)
async def execute_paper_trade(trade: PaperTradeCreate, current_user: dict = Depends(get_current_user)):
    """Execute a paper trade"""
    user_id = current_user["id"]
    
    # Get current balance and portfolio
    user = await db.users.find_one({"id": user_id})
    balance = user.get("paper_balance", 10000.0)
    portfolio = user.get("portfolio", {})
    
    total_cost = trade.amount * trade.price
    
    if trade.type == "buy":
        if total_cost > balance:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        new_balance = balance - total_cost
        current_holding = portfolio.get(trade.symbol, {"amount": 0, "avg_price": 0})
        
        # Calculate new average price
        total_amount = current_holding["amount"] + trade.amount
        if total_amount > 0:
            new_avg_price = ((current_holding["amount"] * current_holding["avg_price"]) + total_cost) / total_amount
        else:
            new_avg_price = trade.price
        
        portfolio[trade.symbol] = {"amount": total_amount, "avg_price": new_avg_price}
        
    elif trade.type == "sell":
        current_holding = portfolio.get(trade.symbol, {"amount": 0})
        if current_holding["amount"] < trade.amount:
            raise HTTPException(status_code=400, detail="Insufficient holdings")
        
        new_balance = balance + total_cost
        remaining = current_holding["amount"] - trade.amount
        
        if remaining > 0:
            portfolio[trade.symbol] = {"amount": remaining, "avg_price": current_holding.get("avg_price", trade.price)}
        else:
            portfolio.pop(trade.symbol, None)
    else:
        raise HTTPException(status_code=400, detail="Invalid trade type")
    
    # Update user balance and portfolio
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"paper_balance": new_balance, "portfolio": portfolio}}
    )
    
    # Record trade
    trade_id = str(uuid.uuid4())
    trade_doc = {
        "id": trade_id,
        "user_id": user_id,
        "symbol": trade.symbol,
        "type": trade.type,
        "amount": trade.amount,
        "price": trade.price,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "executed"
    }
    await db.paper_trades.insert_one(trade_doc)
    
    return PaperTrade(**trade_doc)

@api_router.get("/paper-trading/trades")
async def get_paper_trades(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get paper trading history"""
    trades = await db.paper_trades.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    return trades

@api_router.get("/paper-trading/portfolio")
async def get_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Get paper trading portfolio"""
    user = await db.users.find_one({"id": current_user["id"]})
    return {
        "balance": user.get("paper_balance", 10000.0),
        "portfolio": user.get("portfolio", {}),
        "initial_balance": 10000.0
    }

@api_router.post("/paper-trading/reset")
async def reset_paper_portfolio(current_user: dict = Depends(get_current_user)):
    """Reset paper trading portfolio"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"paper_balance": 10000.0, "portfolio": {}}}
    )
    await db.paper_trades.delete_many({"user_id": current_user["id"]})
    return {"message": "Portfolio reset successfully", "balance": 10000.0}

# ============== WATCHLIST ROUTES ==============

@api_router.put("/watchlist")
async def update_watchlist(data: WatchlistUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"watchlist": data.symbols}}
    )
    return {"watchlist": data.symbols}

@api_router.post("/watchlist/{symbol}")
async def add_to_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """Add symbol to watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$addToSet": {"watchlist": symbol.lower()}}
    )
    user = await db.users.find_one({"id": current_user["id"]})
    return {"watchlist": user.get("watchlist", [])}

@api_router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """Remove symbol from watchlist"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"watchlist": symbol.lower()}}
    )
    user = await db.users.find_one({"id": current_user["id"]})
    return {"watchlist": user.get("watchlist", [])}

# ============== ALERTS ROUTES ==============

@api_router.post("/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a price alert"""
    alert_id = str(uuid.uuid4())
    alert_doc = {
        "id": alert_id,
        "user_id": current_user["id"],
        "symbol": alert.symbol.lower(),
        "target_price": alert.target_price,
        "condition": alert.condition,
        "name": alert.name or f"Alert {alert.symbol.upper()} {alert.condition} ${alert.target_price}",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.alerts.insert_one(alert_doc)
    return AlertResponse(**alert_doc)

@api_router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    """Get all alerts for current user"""
    alerts = await db.alerts.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    return alerts

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an alert"""
    result = await db.alerts.delete_one({"id": alert_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted"}

# ============== STRATEGIES ROUTES ==============

@api_router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, current_user: dict = Depends(get_current_user)):
    """Create a trading strategy"""
    strategy_id = str(uuid.uuid4())
    strategy_doc = {
        "id": strategy_id,
        "user_id": current_user["id"],
        "name": strategy.name,
        "description": strategy.description,
        "indicators": strategy.indicators,
        "entry_rules": strategy.entry_rules,
        "exit_rules": strategy.exit_rules,
        "risk_percentage": strategy.risk_percentage,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.strategies.insert_one(strategy_doc)
    return StrategyResponse(**strategy_doc)

@api_router.get("/strategies")
async def get_strategies(current_user: dict = Depends(get_current_user)):
    """Get all strategies for current user"""
    strategies = await db.strategies.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    return strategies

@api_router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a strategy"""
    result = await db.strategies.delete_one({"id": strategy_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"message": "Strategy deleted"}

# ============== USER SETTINGS ROUTES ==============

@api_router.put("/settings/trading-level")
async def update_trading_level(level: str, current_user: dict = Depends(get_current_user)):
    """Update user's trading level"""
    if level not in ["beginner", "intermediate", "advanced"]:
        raise HTTPException(status_code=400, detail="Invalid trading level")
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"trading_level": level}}
    )
    return {"trading_level": level}

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "BULL SAGE API is running", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ============== ADMIN ROUTES ==============

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Verify the user is an admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@api_router.get("/admin/users")
async def admin_get_users(admin: dict = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.get("/admin/stats")
async def admin_get_stats(admin: dict = Depends(get_admin_user)):
    """Get platform statistics (admin only)"""
    users_count = await db.users.count_documents({})
    trades_count = await db.paper_trades.count_documents({})
    strategies_count = await db.strategies.count_documents({})
    alerts_count = await db.alerts.count_documents({})
    chats_count = await db.chat_history.count_documents({})
    
    return {
        "users": users_count,
        "paper_trades": trades_count,
        "strategies": strategies_count,
        "alerts": alerts_count,
        "ai_chats": chats_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a user (admin only)"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clean up user data
    await db.paper_trades.delete_many({"user_id": user_id})
    await db.strategies.delete_many({"user_id": user_id})
    await db.alerts.delete_many({"user_id": user_id})
    await db.chat_history.delete_many({"user_id": user_id})
    
    return {"message": "User deleted successfully"}

@api_router.put("/admin/users/{user_id}/admin")
async def admin_toggle_admin(user_id: str, is_admin: bool, admin: dict = Depends(get_admin_user)):
    """Toggle admin status for a user (admin only)"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin status")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": is_admin}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"Admin status {'granted' if is_admin else 'revoked'}"}

@api_router.get("/admin/api-keys")
async def get_api_keys(admin: dict = Depends(get_admin_user)):
    """Get all configured API keys (admin only) - masked for security"""
    def mask_key(key: str) -> dict:
        if not key:
            return {"masked": "Non configurée", "full": "", "configured": False}
        if len(key) > 8:
            masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
        else:
            masked = "*" * len(key)
        return {"masked": masked, "full": key, "configured": True}
    
    return {
        "coingecko": {"masked": "Gratuit (pas de clé)", "full": "", "configured": True, "name": "CoinGecko", "usage": "Données crypto"},
        "alpha_vantage": {**mask_key(ALPHA_VANTAGE_API_KEY), "name": "Alpha Vantage", "usage": "Forex, Actions, Indicateurs"},
        "finnhub": {**mask_key(FINNHUB_API_KEY), "name": "Finnhub", "usage": "News, Sentiment, Calendrier éco"},
        "fred": {**mask_key(FRED_API_KEY), "name": "FRED", "usage": "Données macro (Fed, Inflation, PIB)"},
        "marketaux": {**mask_key(MARKETAUX_API_KEY), "name": "Marketaux", "usage": "News sentiment avancé"},
        "emergent_llm": {**mask_key(EMERGENT_LLM_KEY), "name": "Emergent LLM", "usage": "IA GPT-5.1"}
    }

# ============== STARTUP EVENTS ==============

@app.on_event("startup")
async def create_admin_user():
    """Create default admin user on startup"""
    admin_email = "coachdigitalparis@gmail.com"
    admin_password = "$$Reussite888!!"
    
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin_id = str(uuid.uuid4())
        admin_doc = {
            "id": admin_id,
            "email": admin_email,
            "password": hash_password(admin_password),
            "name": "Admin Coach Digital",
            "trading_level": "advanced",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "paper_balance": 10000.0,
            "watchlist": ["bitcoin", "ethereum", "solana", "cardano", "polkadot"],
            "portfolio": {},
            "is_admin": True
        }
        await db.users.insert_one(admin_doc)
        logger.info(f"Admin user created: {admin_email}")
    else:
        # Ensure existing user has admin status
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"is_admin": True}}
        )
        logger.info(f"Admin status confirmed for: {admin_email}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
