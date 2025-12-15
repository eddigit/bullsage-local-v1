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

@api_router.get("/market/crypto")
async def get_crypto_markets(current_user: dict = Depends(get_current_user)):
    """Get top cryptocurrencies from CoinGecko"""
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
                return response.json()
            else:
                logger.error(f"CoinGecko API error: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching crypto markets: {e}")
        return []

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
                    data["fear_greed"] = fng["data"][0]
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")

        # 3. Market News from Finnhub
        try:
            response = await client.get(
                "https://finnhub.io/api/v1/news",
                params={"category": "crypto", "token": FINNHUB_API_KEY},
                timeout=15.0
            )
            if response.status_code == 200:
                news = response.json()
                data["news"] = news[:5] if news else []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

        # 4. Macro data from FRED
        try:
            # VIX
            response = await client.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "VIXCLS",
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1
                },
                timeout=10.0
            )
            if response.status_code == 200:
                vix_data = response.json()
                if vix_data.get("observations"):
                    data["macro"]["vix"] = vix_data["observations"][0].get("value")
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")

        try:
            # Fed Rate
            response = await client.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "FEDFUNDS",
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1
                },
                timeout=10.0
            )
            if response.status_code == 200:
                fed_data = response.json()
                if fed_data.get("observations"):
                    data["macro"]["fed_rate"] = fed_data["observations"][0].get("value")
        except Exception as e:
            logger.error(f"Error fetching Fed rate: {e}")

    return data

@api_router.post("/assistant/chat", response_model=ChatResponse)
async def chat_with_bull(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat with BULL SAGE AI Assistant - with real-time market data"""
    try:
        # Get user's trading level for personalized responses
        trading_level = current_user.get("trading_level", "beginner")
        user_name = current_user.get("name", "Trader")
        
        # FETCH ALL REAL-TIME DATA
        market_data = await fetch_realtime_market_data()
        
        # Build comprehensive market context
        market_context = f"""
=== DONNÉES MARCHÉ TEMPS RÉEL ({market_data['timestamp'][:19].replace('T', ' ')} UTC) ===

📊 PRIX CRYPTO ACTUELS:"""
        
        for coin in market_data["crypto"]:
            price = coin.get("current_price", 0)
            change_1h = coin.get("price_change_percentage_1h_in_currency", 0) or 0
            change_24h = coin.get("price_change_percentage_24h", 0) or 0
            change_7d = coin.get("price_change_percentage_7d_in_currency", 0) or 0
            high_24h = coin.get("high_24h", 0)
            low_24h = coin.get("low_24h", 0)
            market_context += f"""
- {coin['name']} ({coin['symbol'].upper()}): ${price:,.2f}
  • 1h: {change_1h:+.2f}% | 24h: {change_24h:+.2f}% | 7j: {change_7d:+.2f}%
  • High 24h: ${high_24h:,.2f} | Low 24h: ${low_24h:,.2f}"""

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

🏦 DONNÉES MACRO (FRED):
- VIX (Volatilité): {market_data['macro'].get('vix', 'N/A')}"""
            vix = market_data['macro'].get('vix')
            if vix:
                try:
                    vix_val = float(vix)
                    if vix_val < 15:
                        market_context += " (Faible volatilité - marché calme)"
                    elif vix_val < 25:
                        market_context += " (Volatilité normale)"
                    else:
                        market_context += " (Haute volatilité - ATTENTION)"
                except:
                    pass
            market_context += f"""
- Taux Fed: {market_data['macro'].get('fed_rate', 'N/A')}%"""

        # News headlines
        if market_data["news"]:
            market_context += """

📰 DERNIÈRES NEWS CRYPTO:"""
            for news in market_data["news"][:3]:
                headline = news.get("headline", "")[:100]
                market_context += f"""
- {headline}"""

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
