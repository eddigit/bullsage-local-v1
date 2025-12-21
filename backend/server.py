from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
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
BINANCE_API_URL = "https://api.binance.com/api/v3"
CRYPTOCOMPARE_API_URL = "https://min-api.cryptocompare.com/data"
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
    onboarding_completed: bool = False
    preferences: Optional[Dict[str, Any]] = None

class UserPreferences(BaseModel):
    experience_level: str  # beginner, intermediate, confirmed, expert
    preferred_markets: List[str]  # crypto, forex, stocks, indices, commodities, defi
    trading_goals: List[str]  # learn, speculate, invest, automate, analyze
    favorite_cryptos: List[str] = []
    favorite_forex: List[str] = []
    favorite_stocks: List[str] = []
    favorite_indices: List[str] = []
    favorite_commodities: List[str] = []

class OnboardingData(BaseModel):
    experience_level: str
    preferred_markets: List[str]
    trading_goals: List[str]
    favorite_assets: Dict[str, List[str]] = {}

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

# ============== TRADING JOURNAL MODELS ==============

class TradeJournalEntry(BaseModel):
    id: str
    user_id: str
    # Trade info
    symbol: str
    symbol_name: str
    trade_type: str  # BUY or SELL
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    # Timing
    entry_date: str
    exit_date: Optional[str] = None
    timeframe: str
    # Risk management
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    # Results
    status: str = "open"  # open, closed_profit, closed_loss, closed_breakeven
    pnl_amount: Optional[float] = None
    pnl_percent: Optional[float] = None
    # Psychology
    emotion_before: Optional[str] = None  # calm, anxious, excited, fearful, confident
    emotion_after: Optional[str] = None
    # Learning
    strategy_used: Optional[str] = None
    reason_entry: str
    reason_exit: Optional[str] = None
    lessons_learned: Optional[str] = None
    screenshot_url: Optional[str] = None
    # Meta
    created_at: str
    updated_at: Optional[str] = None

class TradeJournalCreate(BaseModel):
    symbol: str
    symbol_name: str
    trade_type: str
    entry_price: float
    quantity: float
    timeframe: str
    stop_loss: float
    take_profit: float
    emotion_before: Optional[str] = None
    strategy_used: Optional[str] = None
    reason_entry: str

class TradeJournalClose(BaseModel):
    exit_price: float
    emotion_after: Optional[str] = None
    reason_exit: Optional[str] = None
    lessons_learned: Optional[str] = None

# ============== ADVANCED ALERTS MODELS ==============

class SmartAlertCreate(BaseModel):
    symbol: str
    symbol_name: str
    alert_type: str  # price, rsi, macd, support, resistance, custom
    condition: str  # above, below, crosses_up, crosses_down
    value: float
    message: Optional[str] = None
    sound_enabled: bool = True
    repeat: bool = False

class SmartAlertResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    symbol_name: str
    alert_type: str
    condition: str
    value: float
    message: str
    sound_enabled: bool
    repeat: bool
    triggered: bool
    triggered_at: Optional[str] = None
    created_at: str

# ============== DAILY BRIEFING MODEL ==============

class DailyBriefing(BaseModel):
    date: str
    market_sentiment: str  # bullish, bearish, neutral
    fear_greed: int
    key_levels: Dict[str, Any]
    opportunities: List[Dict[str, Any]]
    risks: List[str]
    recommended_actions: List[str]
    ai_summary: str

# ============== TRADING STATS MODEL ==============

class TradingStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_win: float
    average_loss: float
    best_trade: float
    worst_trade: float
    profit_factor: float
    average_rr: float
    most_traded_symbol: str
    best_timeframe: str
    best_day_of_week: str
    current_streak: int
    max_drawdown: float

# ============== ACADEMY MODELS ==============

class AcademyProgress(BaseModel):
    user_id: str
    total_xp: int = 0
    level: int = 1
    level_title: str = "Nouveau Venu"
    level_icon: str = "🌱"
    completed_lessons: List[str] = []
    completed_quizzes: List[str] = []
    quiz_scores: Dict[str, int] = {}
    badges: List[str] = []
    streak_days: int = 0
    last_activity: Optional[str] = None
    daily_xp_earned: int = 0

class QuizSubmission(BaseModel):
    lesson_id: str
    answers: Dict[str, int]  # question_id: selected_answer_index

class QuizResult(BaseModel):
    score: int
    total: int
    percentage: float
    passed: bool
    xp_earned: int
    badges_earned: List[str]
    correct_answers: Dict[str, bool]
    explanations: Dict[str, str]

class LessonComplete(BaseModel):
    lesson_id: str

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

# Robust multi-source cache for crypto data
_crypto_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 300,  # Cache for 5 minutes (300 seconds)
    "source": None
}

# Mapping between CoinGecko IDs and Binance symbols
CRYPTO_MAPPING = {
    "bitcoin": {"symbol": "BTCUSDT", "name": "Bitcoin", "binance_symbol": "BTC", "rank": 1, "image": "https://coin-images.coingecko.com/coins/images/1/large/bitcoin.png"},
    "ethereum": {"symbol": "ETHUSDT", "name": "Ethereum", "binance_symbol": "ETH", "rank": 2, "image": "https://coin-images.coingecko.com/coins/images/279/large/ethereum.png"},
    "binancecoin": {"symbol": "BNBUSDT", "name": "BNB", "binance_symbol": "BNB", "rank": 3, "image": "https://coin-images.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"},
    "solana": {"symbol": "SOLUSDT", "name": "Solana", "binance_symbol": "SOL", "rank": 4, "image": "https://coin-images.coingecko.com/coins/images/4128/large/solana.png"},
    "ripple": {"symbol": "XRPUSDT", "name": "XRP", "binance_symbol": "XRP", "rank": 5, "image": "https://coin-images.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"},
    "cardano": {"symbol": "ADAUSDT", "name": "Cardano", "binance_symbol": "ADA", "rank": 6, "image": "https://coin-images.coingecko.com/coins/images/975/large/cardano.png"},
    "dogecoin": {"symbol": "DOGEUSDT", "name": "Dogecoin", "binance_symbol": "DOGE", "rank": 7, "image": "https://coin-images.coingecko.com/coins/images/5/large/dogecoin.png"},
    "avalanche-2": {"symbol": "AVAXUSDT", "name": "Avalanche", "binance_symbol": "AVAX", "rank": 8, "image": "https://coin-images.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png"},
    "polkadot": {"symbol": "DOTUSDT", "name": "Polkadot", "binance_symbol": "DOT", "rank": 9, "image": "https://coin-images.coingecko.com/coins/images/12171/large/polkadot.png"},
    "chainlink": {"symbol": "LINKUSDT", "name": "Chainlink", "binance_symbol": "LINK", "rank": 10, "image": "https://coin-images.coingecko.com/coins/images/877/large/chainlink-new-logo.png"},
    "polygon": {"symbol": "MATICUSDT", "name": "Polygon", "binance_symbol": "MATIC", "rank": 11, "image": "https://coin-images.coingecko.com/coins/images/4713/large/polygon.png"},
    "litecoin": {"symbol": "LTCUSDT", "name": "Litecoin", "binance_symbol": "LTC", "rank": 12, "image": "https://coin-images.coingecko.com/coins/images/2/large/litecoin.png"},
    "shiba-inu": {"symbol": "SHIBUSDT", "name": "Shiba Inu", "binance_symbol": "SHIB", "rank": 13, "image": "https://coin-images.coingecko.com/coins/images/11939/large/shiba.png"},
    "uniswap": {"symbol": "UNIUSDT", "name": "Uniswap", "binance_symbol": "UNI", "rank": 14, "image": "https://coin-images.coingecko.com/coins/images/12504/large/uni.jpg"},
    "near": {"symbol": "NEARUSDT", "name": "NEAR Protocol", "binance_symbol": "NEAR", "rank": 15, "image": "https://coin-images.coingecko.com/coins/images/10365/large/near.jpg"},
    "tron": {"symbol": "TRXUSDT", "name": "TRON", "binance_symbol": "TRX", "rank": 16, "image": "https://coin-images.coingecko.com/coins/images/1094/large/tron-logo.png"},
    "stellar": {"symbol": "XLMUSDT", "name": "Stellar", "binance_symbol": "XLM", "rank": 17, "image": "https://coin-images.coingecko.com/coins/images/100/large/Stellar_symbol_black_RGB.png"},
    "cosmos": {"symbol": "ATOMUSDT", "name": "Cosmos", "binance_symbol": "ATOM", "rank": 18, "image": "https://coin-images.coingecko.com/coins/images/1481/large/cosmos_hub.png"},
    "ethereum-classic": {"symbol": "ETCUSDT", "name": "Ethereum Classic", "binance_symbol": "ETC", "rank": 19, "image": "https://coin-images.coingecko.com/coins/images/453/large/ethereum-classic-logo.png"},
    "filecoin": {"symbol": "FILUSDT", "name": "Filecoin", "binance_symbol": "FIL", "rank": 20, "image": "https://coin-images.coingecko.com/coins/images/12817/large/filecoin.png"},
}

async def fetch_crypto_from_binance():
    """
    Fetch real-time crypto data from Binance API (PRIMARY SOURCE)
    Binance has generous rate limits: 1200 requests/minute
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get 24hr ticker for all symbols we need
            symbols = [info["symbol"] for info in CRYPTO_MAPPING.values()]
            
            # Binance ticker endpoint - very reliable
            response = await client.get(
                f"{BINANCE_API_URL}/ticker/24hr",
                timeout=15.0
            )
            
            if response.status_code != 200:
                logger.warning(f"Binance API returned {response.status_code}")
                return None
            
            binance_data = response.json()
            
            # Create a lookup map
            binance_lookup = {item["symbol"]: item for item in binance_data}
            
            # Build crypto list in CoinGecko-compatible format
            crypto_list = []
            for coin_id, info in CRYPTO_MAPPING.items():
                binance_symbol = info["symbol"]
                if binance_symbol in binance_lookup:
                    ticker = binance_lookup[binance_symbol]
                    crypto_list.append({
                        "id": coin_id,
                        "symbol": info["binance_symbol"].lower(),
                        "name": info["name"],
                        "image": info["image"],
                        "current_price": float(ticker["lastPrice"]),
                        "market_cap": float(ticker["quoteVolume"]) * 100,  # Approximate
                        "market_cap_rank": info["rank"],
                        "price_change_percentage_24h": float(ticker["priceChangePercent"]),
                        "high_24h": float(ticker["highPrice"]),
                        "low_24h": float(ticker["lowPrice"]),
                        "total_volume": float(ticker["volume"]),
                        "sparkline_in_7d": {"price": []},
                        "source": "binance"
                    })
            
            # Sort by rank
            crypto_list.sort(key=lambda x: x["market_cap_rank"])
            
            logger.info(f"✅ Fetched {len(crypto_list)} cryptos from Binance")
            return crypto_list
            
    except Exception as e:
        logger.error(f"Binance API error: {e}")
        return None

async def fetch_crypto_from_coingecko():
    """
    Fetch crypto data from CoinGecko API (SECONDARY SOURCE)
    Has rate limits but provides more detailed data
    """
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
                # Add source marker
                for item in data:
                    item["source"] = "coingecko"
                logger.info(f"✅ Fetched {len(data)} cryptos from CoinGecko")
                return data
            elif response.status_code == 429:
                logger.warning("CoinGecko rate limited")
                return None
            else:
                logger.warning(f"CoinGecko returned {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"CoinGecko API error: {e}")
        return None

async def fetch_crypto_from_cryptocompare():
    """
    Fetch real-time crypto data from CryptoCompare API (RELIABLE FALLBACK)
    Free tier: 100,000 calls/month, no geographic restrictions
    """
    try:
        # List of top cryptos to fetch
        symbols = "BTC,ETH,BNB,SOL,XRP,ADA,DOGE,AVAX,DOT,LINK,MATIC,LTC,SHIB,UNI,NEAR,TRX,XLM,ATOM,ETC,FIL"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CRYPTOCOMPARE_API_URL}/pricemultifull",
                params={
                    "fsyms": symbols,
                    "tsyms": "USD"
                },
                timeout=15.0
            )
            
            if response.status_code != 200:
                logger.warning(f"CryptoCompare returned {response.status_code}")
                return None
            
            data = response.json()
            
            if "RAW" not in data:
                logger.warning("CryptoCompare: No RAW data in response")
                return None
            
            # Symbol to CoinGecko ID mapping
            symbol_to_id = {
                "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
                "SOL": "solana", "XRP": "ripple", "ADA": "cardano",
                "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot",
                "LINK": "chainlink", "MATIC": "polygon", "LTC": "litecoin",
                "SHIB": "shiba-inu", "UNI": "uniswap", "NEAR": "near",
                "TRX": "tron", "XLM": "stellar", "ATOM": "cosmos",
                "ETC": "ethereum-classic", "FIL": "filecoin"
            }
            
            crypto_list = []
            rank = 1
            
            for symbol, info in data["RAW"].items():
                if "USD" not in info:
                    continue
                    
                usd_data = info["USD"]
                coin_id = symbol_to_id.get(symbol, symbol.lower())
                
                # Get image from CRYPTO_MAPPING if available
                image = ""
                if coin_id in CRYPTO_MAPPING:
                    image = CRYPTO_MAPPING[coin_id]["image"]
                
                crypto_list.append({
                    "id": coin_id,
                    "symbol": symbol.lower(),
                    "name": usd_data.get("FROMSYMBOL", symbol),
                    "image": image,
                    "current_price": usd_data.get("PRICE", 0),
                    "market_cap": usd_data.get("MKTCAP", 0),
                    "market_cap_rank": rank,
                    "price_change_percentage_24h": usd_data.get("CHANGEPCT24HOUR", 0),
                    "high_24h": usd_data.get("HIGH24HOUR", 0),
                    "low_24h": usd_data.get("LOW24HOUR", 0),
                    "total_volume": usd_data.get("TOTALVOLUME24HTO", 0),
                    "sparkline_in_7d": {"price": []},
                    "source": "cryptocompare"
                })
                rank += 1
            
            # Sort by market cap
            crypto_list.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
            
            # Re-assign ranks after sorting
            for i, crypto in enumerate(crypto_list):
                crypto["market_cap_rank"] = i + 1
            
            logger.info(f"✅ Fetched {len(crypto_list)} cryptos from CryptoCompare")
            return crypto_list
            
    except Exception as e:
        logger.error(f"CryptoCompare API error: {e}")
        return None

@api_router.get("/market/crypto")
async def get_crypto_markets(current_user: dict = Depends(get_current_user)):
    """
    Get top cryptocurrencies - REAL DATA ONLY
    Uses Binance as primary source (more reliable), CoinGecko as fallback
    """
    global _crypto_cache
    
    now = datetime.now(timezone.utc)
    
    # Check cache first (5 minutes TTL)
    if _crypto_cache["data"] and _crypto_cache["timestamp"]:
        age = (now - _crypto_cache["timestamp"]).total_seconds()
        if age < _crypto_cache["ttl"]:
            logger.info(f"Returning cached crypto data (source: {_crypto_cache.get('source', 'unknown')})")
            return _crypto_cache["data"]
    
    # Strategy 1: Try CryptoCompare first (most reliable, no rate limits, no geo-blocking)
    cryptocompare_data = await fetch_crypto_from_cryptocompare()
    if cryptocompare_data and len(cryptocompare_data) > 0:
        _crypto_cache["data"] = cryptocompare_data
        _crypto_cache["timestamp"] = now
        _crypto_cache["source"] = "cryptocompare"
        return cryptocompare_data
    
    # Strategy 2: Try CoinGecko as fallback
    coingecko_data = await fetch_crypto_from_coingecko()
    if coingecko_data and len(coingecko_data) > 0:
        _crypto_cache["data"] = coingecko_data
        _crypto_cache["timestamp"] = now
        _crypto_cache["source"] = "coingecko"
        return coingecko_data
    
    # Strategy 3: Try Binance (may be geo-blocked)
    binance_data = await fetch_crypto_from_binance()
    if binance_data and len(binance_data) > 0:
        _crypto_cache["data"] = binance_data
        _crypto_cache["timestamp"] = now
        _crypto_cache["source"] = "binance"
        return binance_data
    
    # Strategy 4: Return stale cache if available (real data, just old)
    if _crypto_cache["data"]:
        logger.warning("Returning stale cached data - all APIs unavailable")
        return _crypto_cache["data"]
    
    # No data available at all
    raise HTTPException(
        status_code=503,
        detail="Les APIs de données crypto sont temporairement indisponibles. Veuillez réessayer dans quelques minutes."
    )

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
        
        user_msg = UserMessage(text=f"Analyse ces actualités crypto des dernières 48h et résume en français avec impact marché:\n\n{news_text}")
        ai_response = await chat.send_message(user_msg)
        
        # Parse AI response - the response is a string directly
        response_text = str(ai_response) if ai_response else ""
        
        logger.info(f"AI news response preview: {response_text[:300] if response_text else 'empty'}")
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\[[\s\S]*?\]', response_text)
        if json_match:
            import json
            try:
                summary_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                summary_data = [{"news": "Parsing error", "impact": "NEUTRE", "action": "Surveiller le marché"}]
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
    """Get comprehensive trading signal statistics with professional metrics"""
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
            "total_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "best_signal": None,
            "worst_signal": None,
            "current_streak": 0,
            "max_streak": 0,
            "by_symbol": {},
            "by_timeframe": {},
            "monthly_performance": [],
            "recent_signals": []
        }
    
    active = len([s for s in signals if s["status"] == "active"])
    hit_tp1 = len([s for s in signals if s["status"] == "hit_tp1"])
    hit_tp2 = len([s for s in signals if s["status"] == "hit_tp2"])
    hit_sl = len([s for s in signals if s["status"] == "hit_sl"])
    expired = len([s for s in signals if s["status"] == "expired"])
    
    completed = hit_tp1 + hit_tp2 + hit_sl
    wins = hit_tp1 + hit_tp2
    win_rate = (wins / completed * 100) if completed > 0 else 0
    
    # P&L Analysis
    closed_signals = [s for s in signals if s.get("result_pnl") is not None]
    pnl_values = [s.get("result_pnl", 0) for s in closed_signals]
    
    total_pnl = sum(pnl_values) if pnl_values else 0
    win_pnls = [p for p in pnl_values if p > 0]
    loss_pnls = [p for p in pnl_values if p < 0]
    
    avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
    avg_loss = abs(sum(loss_pnls) / len(loss_pnls)) if loss_pnls else 0
    
    gross_profit = sum(win_pnls) if win_pnls else 0
    gross_loss = abs(sum(loss_pnls)) if loss_pnls else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
    
    # Best and worst signals
    best_signal = None
    worst_signal = None
    if closed_signals:
        sorted_by_pnl = sorted(closed_signals, key=lambda x: x.get("result_pnl", 0), reverse=True)
        if sorted_by_pnl:
            best = sorted_by_pnl[0]
            best_signal = {"symbol": best.get("symbol_name"), "pnl": best.get("result_pnl", 0), "type": best.get("signal_type")}
            worst = sorted_by_pnl[-1]
            worst_signal = {"symbol": worst.get("symbol_name"), "pnl": worst.get("result_pnl", 0), "type": worst.get("signal_type")}
    
    # Streak calculation
    sorted_signals = sorted([s for s in signals if s["status"] != "active"], key=lambda x: x.get("created_at", ""), reverse=True)
    current_streak = 0
    max_streak = 0
    temp_streak = 0
    last_result = None
    
    for s in sorted_signals:
        is_win = s["status"] in ["hit_tp1", "hit_tp2"]
        if last_result is None:
            last_result = is_win
            current_streak = 1 if is_win else -1
            temp_streak = 1
        elif is_win == last_result:
            temp_streak += 1
            if current_streak > 0:
                current_streak = temp_streak
            else:
                current_streak = -temp_streak
        else:
            max_streak = max(max_streak, abs(temp_streak))
            temp_streak = 1
            last_result = is_win
            current_streak = 1 if is_win else -1
    max_streak = max(max_streak, abs(temp_streak))
    
    # Stats by symbol with P&L
    by_symbol = {}
    for s in signals:
        sym = s["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = {"total": 0, "wins": 0, "pnl": 0, "name": s.get("symbol_name", sym)}
        by_symbol[sym]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_symbol[sym]["wins"] += 1
        if s.get("result_pnl"):
            by_symbol[sym]["pnl"] += s["result_pnl"]
    
    # Calculate win rate for each symbol
    for sym in by_symbol:
        if by_symbol[sym]["total"] > 0:
            by_symbol[sym]["win_rate"] = round(by_symbol[sym]["wins"] / by_symbol[sym]["total"] * 100, 1)
        else:
            by_symbol[sym]["win_rate"] = 0
        by_symbol[sym]["pnl"] = round(by_symbol[sym]["pnl"], 2)
    
    # Stats by timeframe
    by_timeframe = {}
    for s in signals:
        tf = s["timeframe"]
        if tf not in by_timeframe:
            by_timeframe[tf] = {"total": 0, "wins": 0, "pnl": 0}
        by_timeframe[tf]["total"] += 1
        if s["status"] in ["hit_tp1", "hit_tp2"]:
            by_timeframe[tf]["wins"] += 1
        if s.get("result_pnl"):
            by_timeframe[tf]["pnl"] += s["result_pnl"]
    
    for tf in by_timeframe:
        if by_timeframe[tf]["total"] > 0:
            by_timeframe[tf]["win_rate"] = round(by_timeframe[tf]["wins"] / by_timeframe[tf]["total"] * 100, 1)
        by_timeframe[tf]["pnl"] = round(by_timeframe[tf]["pnl"], 2)
    
    # Monthly performance (last 6 months)
    from collections import defaultdict
    monthly_perf = defaultdict(lambda: {"signals": 0, "wins": 0, "pnl": 0})
    for s in closed_signals:
        if s.get("created_at"):
            month = s["created_at"][:7]  # YYYY-MM
            monthly_perf[month]["signals"] += 1
            if s["status"] in ["hit_tp1", "hit_tp2"]:
                monthly_perf[month]["wins"] += 1
            monthly_perf[month]["pnl"] += s.get("result_pnl", 0)
    
    monthly_performance = []
    for month, data in sorted(monthly_perf.items(), reverse=True)[:6]:
        monthly_performance.append({
            "month": month,
            "signals": data["signals"],
            "wins": data["wins"],
            "win_rate": round(data["wins"] / data["signals"] * 100, 1) if data["signals"] > 0 else 0,
            "pnl": round(data["pnl"], 2)
        })
    
    # Recent 5 closed signals
    recent_signals = []
    for s in sorted_signals[:5]:
        recent_signals.append({
            "symbol": s.get("symbol_name"),
            "type": s.get("signal_type"),
            "status": s.get("status"),
            "pnl": s.get("result_pnl", 0),
            "date": s.get("created_at", "")[:10]
        })
    
    return {
        "total_signals": total,
        "active": active,
        "hit_tp1": hit_tp1,
        "hit_tp2": hit_tp2,
        "hit_sl": hit_sl,
        "expired": expired,
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "best_signal": best_signal,
        "worst_signal": worst_signal,
        "current_streak": current_streak,
        "max_streak": max_streak,
        "by_symbol": by_symbol,
        "by_timeframe": by_timeframe,
        "monthly_performance": monthly_performance,
        "recent_signals": recent_signals
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

# ============== TRADING JOURNAL ROUTES ==============

@api_router.post("/journal/trades")
async def create_journal_entry(entry: TradeJournalCreate, current_user: dict = Depends(get_current_user)):
    """Create a new trade journal entry"""
    # Calculate risk/reward ratio
    if entry.trade_type == "BUY":
        risk = entry.entry_price - entry.stop_loss
        reward = entry.take_profit - entry.entry_price
    else:
        risk = entry.stop_loss - entry.entry_price
        reward = entry.entry_price - entry.take_profit
    
    rr_ratio = round(reward / risk, 2) if risk > 0 else 0
    
    journal_entry = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "symbol": entry.symbol,
        "symbol_name": entry.symbol_name,
        "trade_type": entry.trade_type,
        "entry_price": entry.entry_price,
        "exit_price": None,
        "quantity": entry.quantity,
        "entry_date": datetime.now(timezone.utc).isoformat(),
        "exit_date": None,
        "timeframe": entry.timeframe,
        "stop_loss": entry.stop_loss,
        "take_profit": entry.take_profit,
        "risk_reward_ratio": rr_ratio,
        "status": "open",
        "pnl_amount": None,
        "pnl_percent": None,
        "emotion_before": entry.emotion_before,
        "emotion_after": None,
        "strategy_used": entry.strategy_used,
        "reason_entry": entry.reason_entry,
        "reason_exit": None,
        "lessons_learned": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.journal.insert_one(journal_entry)
    journal_entry.pop("_id", None)
    return journal_entry

@api_router.get("/journal/trades")
async def get_journal_entries(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get trade journal entries"""
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    entries = await db.journal.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return entries

@api_router.put("/journal/trades/{trade_id}/close")
async def close_journal_trade(trade_id: str, close_data: TradeJournalClose, current_user: dict = Depends(get_current_user)):
    """Close a trade and calculate P&L"""
    trade = await db.journal.find_one({"id": trade_id, "user_id": current_user["id"]}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade["status"] != "open":
        raise HTTPException(status_code=400, detail="Trade already closed")
    
    # Calculate P&L
    if trade["trade_type"] == "BUY":
        pnl_amount = (close_data.exit_price - trade["entry_price"]) * trade["quantity"]
        pnl_percent = ((close_data.exit_price - trade["entry_price"]) / trade["entry_price"]) * 100
    else:
        pnl_amount = (trade["entry_price"] - close_data.exit_price) * trade["quantity"]
        pnl_percent = ((trade["entry_price"] - close_data.exit_price) / trade["entry_price"]) * 100
    
    # Determine status
    if pnl_percent > 0.5:
        status = "closed_profit"
    elif pnl_percent < -0.5:
        status = "closed_loss"
    else:
        status = "closed_breakeven"
    
    update_data = {
        "exit_price": close_data.exit_price,
        "exit_date": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "pnl_amount": round(pnl_amount, 2),
        "pnl_percent": round(pnl_percent, 2),
        "emotion_after": close_data.emotion_after,
        "reason_exit": close_data.reason_exit,
        "lessons_learned": close_data.lessons_learned,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal.update_one({"id": trade_id}, {"$set": update_data})
    return {"message": "Trade closed", "pnl_percent": round(pnl_percent, 2), "status": status}

@api_router.get("/journal/stats")
async def get_trading_stats(current_user: dict = Depends(get_current_user)):
    """Get comprehensive trading statistics"""
    trades = await db.journal.find(
        {"user_id": current_user["id"], "status": {"$ne": "open"}},
        {"_id": 0}
    ).to_list(1000)
    
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "average_win": 0,
            "average_loss": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "profit_factor": 0,
            "average_rr": 0,
            "most_traded_symbol": "N/A",
            "best_timeframe": "N/A",
            "best_day_of_week": "N/A",
            "current_streak": 0,
            "max_drawdown": 0
        }
    
    # Basic stats
    total = len(trades)
    winning = [t for t in trades if t["status"] == "closed_profit"]
    losing = [t for t in trades if t["status"] == "closed_loss"]
    
    win_rate = (len(winning) / total * 100) if total > 0 else 0
    
    # P&L stats
    pnls = [t.get("pnl_percent", 0) for t in trades]
    total_pnl = sum(pnls)
    
    win_pnls = [t.get("pnl_percent", 0) for t in winning]
    loss_pnls = [t.get("pnl_percent", 0) for t in losing]
    
    avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
    avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
    
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    # Profit factor
    gross_profit = sum([p for p in pnls if p > 0])
    gross_loss = abs(sum([p for p in pnls if p < 0]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
    
    # Average R:R
    rrs = [t.get("risk_reward_ratio", 0) for t in trades]
    avg_rr = sum(rrs) / len(rrs) if rrs else 0
    
    # Most traded symbol
    from collections import Counter
    symbols = [t["symbol"] for t in trades]
    most_traded = Counter(symbols).most_common(1)[0][0] if symbols else "N/A"
    
    # Best timeframe (by win rate)
    timeframes = {}
    for t in trades:
        tf = t.get("timeframe", "unknown")
        if tf not in timeframes:
            timeframes[tf] = {"wins": 0, "total": 0}
        timeframes[tf]["total"] += 1
        if t["status"] == "closed_profit":
            timeframes[tf]["wins"] += 1
    
    best_tf = max(timeframes.items(), key=lambda x: x[1]["wins"]/x[1]["total"] if x[1]["total"] > 0 else 0)[0] if timeframes else "N/A"
    
    # Current streak
    sorted_trades = sorted(trades, key=lambda x: x.get("exit_date", ""), reverse=True)
    streak = 0
    streak_type = None
    for t in sorted_trades:
        if streak_type is None:
            streak_type = t["status"]
            streak = 1
        elif t["status"] == streak_type:
            streak += 1
        else:
            break
    
    current_streak = streak if streak_type == "closed_profit" else -streak
    
    # Max drawdown (simplified)
    cumulative = 0
    peak = 0
    max_dd = 0
    for pnl in pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    return {
        "total_trades": total,
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "average_win": round(avg_win, 2),
        "average_loss": round(avg_loss, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "profit_factor": round(profit_factor, 2),
        "average_rr": round(avg_rr, 2),
        "most_traded_symbol": most_traded,
        "best_timeframe": best_tf,
        "best_day_of_week": "N/A",  # Would need more data
        "current_streak": current_streak,
        "max_drawdown": round(max_dd, 2)
    }

# ============== SMART ALERTS ROUTES ==============

@api_router.post("/alerts/smart")
async def create_smart_alert(alert: SmartAlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a smart alert (price, RSI, MACD, etc.)"""
    alert_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "symbol": alert.symbol,
        "symbol_name": alert.symbol_name,
        "alert_type": alert.alert_type,
        "condition": alert.condition,
        "value": alert.value,
        "message": alert.message or f"{alert.symbol_name} {alert.condition} {alert.value}",
        "sound_enabled": alert.sound_enabled,
        "repeat": alert.repeat,
        "triggered": False,
        "triggered_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.smart_alerts.insert_one(alert_doc)
    alert_doc.pop("_id", None)
    return alert_doc

@api_router.get("/alerts/smart")
async def get_smart_alerts(current_user: dict = Depends(get_current_user)):
    """Get all smart alerts for user"""
    alerts = await db.smart_alerts.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return alerts

@api_router.delete("/alerts/smart/{alert_id}")
async def delete_smart_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a smart alert"""
    result = await db.smart_alerts.delete_one({"id": alert_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted"}

@api_router.get("/alerts/check")
async def check_alerts(current_user: dict = Depends(get_current_user)):
    """Check all alerts against current prices and return triggered ones"""
    alerts = await db.smart_alerts.find(
        {"user_id": current_user["id"], "triggered": False},
        {"_id": 0}
    ).to_list(100)
    
    if not alerts:
        return {"triggered": [], "checked": 0}
    
    # Get unique symbols
    symbols = list(set([a["symbol"] for a in alerts]))
    
    # Fetch current prices
    current_prices = {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={"ids": ",".join(symbols), "vs_currencies": "usd"},
                timeout=15.0
            )
            if response.status_code == 200:
                price_data = response.json()
                for symbol, data in price_data.items():
                    current_prices[symbol] = data.get("usd", 0)
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return {"triggered": [], "checked": 0, "error": str(e)}
    
    triggered = []
    for alert in alerts:
        symbol = alert["symbol"]
        current_price = current_prices.get(symbol, 0)
        
        if not current_price:
            continue
        
        is_triggered = False
        
        if alert["alert_type"] == "price":
            if alert["condition"] == "above" and current_price >= alert["value"]:
                is_triggered = True
            elif alert["condition"] == "below" and current_price <= alert["value"]:
                is_triggered = True
        
        if is_triggered:
            # Update alert as triggered
            if not alert["repeat"]:
                await db.smart_alerts.update_one(
                    {"id": alert["id"]},
                    {"$set": {"triggered": True, "triggered_at": datetime.now(timezone.utc).isoformat()}}
                )
            
            triggered.append({
                **alert,
                "current_price": current_price,
                "triggered_at": datetime.now(timezone.utc).isoformat()
            })
    
    return {"triggered": triggered, "checked": len(alerts)}

# ============== DAILY BRIEFING ROUTE ==============

@api_router.get("/briefing/daily")
async def get_daily_briefing(current_user: dict = Depends(get_current_user)):
    """Get AI-generated daily trading briefing"""
    
    # Gather market data
    market_data = {}
    
    async with httpx.AsyncClient() as client:
        # Fear & Greed
        try:
            fg_response = await client.get("https://api.alternative.me/fng/?limit=1", timeout=10.0)
            if fg_response.status_code == 200:
                market_data["fear_greed"] = fg_response.json().get("data", [{}])[0]
        except Exception:
            market_data["fear_greed"] = {"value": "50", "value_classification": "Neutral"}
        
        # BTC price and change
        try:
            btc_response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=10.0
            )
            if btc_response.status_code == 200:
                market_data["prices"] = btc_response.json()
        except Exception:
            market_data["prices"] = {}
    
    # Get user's watchlist performance
    watchlist = current_user.get("watchlist", [])[:5]
    
    # Get recent trades stats
    recent_trades = await db.journal.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    open_trades = [t for t in recent_trades if t.get("status") == "open"]
    
    # Build context for AI
    fg_value = int(market_data.get("fear_greed", {}).get("value", 50))
    fg_class = market_data.get("fear_greed", {}).get("value_classification", "Neutral")
    
    btc_price = market_data.get("prices", {}).get("bitcoin", {}).get("usd", 0)
    btc_change = market_data.get("prices", {}).get("bitcoin", {}).get("usd_24h_change", 0)
    
    context = f"""
BRIEFING MATINAL - {datetime.now().strftime('%d/%m/%Y')}

DONNÉES MARCHÉ:
- Fear & Greed Index: {fg_value} ({fg_class})
- Bitcoin: ${btc_price:,.0f} ({btc_change:+.1f}% 24h)
- Watchlist utilisateur: {', '.join(watchlist) if watchlist else 'Vide'}
- Trades ouverts: {len(open_trades)}

Niveau du trader: {current_user.get('trading_level', 'intermediate')}

Génère un briefing matinal CONCIS et ACTIONNABLE en français:
1. SENTIMENT GÉNÉRAL (1 phrase)
2. OPPORTUNITÉS DU JOUR (2-3 points max)
3. RISQUES À SURVEILLER (2-3 points max)
4. RECOMMANDATION PRINCIPALE (1 action claire)

Format JSON:
{{
  "sentiment": "bullish/bearish/neutral",
  "summary": "Résumé en 2 phrases",
  "opportunities": ["opp1", "opp2"],
  "risks": ["risk1", "risk2"],
  "main_action": "Action principale recommandée",
  "watchlist_focus": "Crypto à surveiller en priorité"
}}
"""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"briefing_{current_user['id']}_{datetime.now().strftime('%Y%m%d')}",
            system_message="Tu es BULL, un trader expert qui donne des briefings matinaux concis et actionnables."
        )
        chat.with_model("openai", "gpt-4o")
        
        user_msg = UserMessage(text=context)
        ai_response = await chat.send_message(user_msg)
        response_text = str(ai_response) if ai_response else ""
        
        # Try to parse JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            import json
            try:
                briefing_data = json.loads(json_match.group())
            except Exception:
                briefing_data = {
                    "sentiment": "neutral",
                    "summary": response_text[:200],
                    "opportunities": [],
                    "risks": [],
                    "main_action": "Analyser le marché",
                    "watchlist_focus": watchlist[0] if watchlist else "bitcoin"
                }
        else:
            briefing_data = {
                "sentiment": "neutral",
                "summary": response_text[:200] if response_text else "Briefing en cours de génération",
                "opportunities": [],
                "risks": [],
                "main_action": "Surveiller le marché",
                "watchlist_focus": watchlist[0] if watchlist else "bitcoin"
            }
        
    except Exception as e:
        logger.error(f"Error generating briefing: {e}")
        briefing_data = {
            "sentiment": "neutral",
            "summary": "Briefing temporairement indisponible",
            "opportunities": [],
            "risks": [],
            "main_action": "Vérifier manuellement le marché",
            "watchlist_focus": "bitcoin"
        }
    
    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "fear_greed": fg_value,
        "fear_greed_label": fg_class,
        "btc_price": btc_price,
        "btc_change_24h": round(btc_change, 2),
        "open_trades": len(open_trades),
        **briefing_data,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ============== TRADING CHECKLIST ROUTE ==============

@api_router.get("/trading/checklist")
async def get_pre_trade_checklist(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get pre-trade checklist for a specific symbol"""
    
    checklist = {
        "symbol": symbol,
        "items": [
            {"id": "trend", "label": "Tendance identifiée (haussière/baissière)", "checked": False},
            {"id": "support", "label": "Niveaux de support/résistance identifiés", "checked": False},
            {"id": "rsi", "label": "RSI vérifié (pas en zone extrême)", "checked": False},
            {"id": "news", "label": "Pas d'annonce majeure imminente", "checked": False},
            {"id": "risk", "label": "Risque limité à 1-2% du capital", "checked": False},
            {"id": "sl", "label": "Stop-loss défini AVANT l'entrée", "checked": False},
            {"id": "tp", "label": "Take-profit défini (R:R min 1:2)", "checked": False},
            {"id": "emotion", "label": "État émotionnel stable", "checked": False},
            {"id": "plan", "label": "Ce trade fait partie de mon plan", "checked": False}
        ],
        "warning": "Ne tradez que si tous les points sont cochés ✓"
    }
    
    return checklist

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

def generate_trading_recommendation(indicators: Dict, current_price: float = None, market_data: Dict = None) -> Dict[str, Any]:
    """Generate professional trading recommendation based on all indicators with entry/exit levels"""
    score = 0
    reasons = []
    risk_factors = []
    
    # RSI Analysis (Weight: 2)
    rsi = indicators.get("rsi", 50)
    if rsi < 25:
        score += 3
        reasons.append(f"🔥 RSI extrême ({rsi}) - Forte survente, rebond probable")
    elif rsi < 30:
        score += 2
        reasons.append(f"RSI en survente ({rsi}) - Signal d'achat")
    elif rsi < 40:
        score += 1
        reasons.append(f"RSI bas ({rsi}) - Potentiel de rebond")
    elif rsi > 75:
        score -= 3
        reasons.append(f"🔥 RSI extrême ({rsi}) - Fort surachat, correction probable")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI en surachat ({rsi}) - Signal de vente")
    elif rsi > 60:
        score -= 1
        reasons.append(f"RSI élevé ({rsi}) - Prudence")
    
    # RSI Divergence (bonus points)
    if 30 < rsi < 40:
        score += 0.5
        reasons.append("RSI en zone d'accumulation")
    
    # MACD Analysis (Weight: 1.5)
    macd = indicators.get("macd", {})
    histogram = macd.get("histogram", 0)
    if macd.get("trend") == "bullish":
        score += 1.5
        if histogram > 0:
            reasons.append(f"MACD haussier avec histogramme positif (+{histogram:.4f})")
        else:
            reasons.append("MACD haussier - Momentum en construction")
    elif macd.get("trend") == "bearish":
        score -= 1.5
        if histogram < 0:
            reasons.append(f"MACD baissier avec histogramme négatif ({histogram:.4f})")
        else:
            reasons.append("MACD baissier - Pression vendeuse")
    
    # Bollinger Analysis (Weight: 2)
    bb = indicators.get("bollinger", {})
    bb_position = bb.get("position", "middle")
    if bb_position == "oversold":
        score += 2.5
        reasons.append("💰 Prix sur bande inférieure Bollinger - Zone d'achat optimale")
    elif bb_position == "lower_half":
        score += 1
        reasons.append("Prix dans la moitié inférieure des Bollinger")
    elif bb_position == "overbought":
        score -= 2.5
        reasons.append("⚠️ Prix sur bande supérieure Bollinger - Zone de prise de profits")
        risk_factors.append("Prix en extension sur les Bollinger")
    elif bb_position == "upper_half":
        score -= 1
        reasons.append("Prix dans la moitié supérieure des Bollinger")
    
    # MA Trend Analysis (Weight: 2)
    ma = indicators.get("moving_averages", {})
    trend = ma.get("trend", "neutral")
    if trend == "strong_bullish":
        score += 2.5
        reasons.append("🚀 Tendance fortement haussière (Golden Cross: MA20 > MA50 > MA200)")
    elif trend == "bullish":
        score += 1.5
        reasons.append("Tendance haussière confirmée")
    elif trend == "strong_bearish":
        score -= 2.5
        reasons.append("⛔ Tendance fortement baissière (Death Cross: MA20 < MA50 < MA200)")
        risk_factors.append("Marché en tendance baissière confirmée")
    elif trend == "bearish":
        score -= 1.5
        reasons.append("Tendance baissière")
    
    # Support/Resistance Proximity
    sr = indicators.get("support_resistance", {})
    support = sr.get("support", 0)
    resistance = sr.get("resistance", 0)
    current = sr.get("current", current_price or 0)
    
    if current and support and resistance:
        range_size = resistance - support
        if range_size > 0:
            position_in_range = (current - support) / range_size
            if position_in_range < 0.2:  # Near support
                score += 1.5
                reasons.append(f"🎯 Prix proche du support ({support:.2f}) - Zone d'achat")
            elif position_in_range > 0.8:  # Near resistance
                score -= 1
                reasons.append(f"Prix proche de la résistance ({resistance:.2f})")
                risk_factors.append("Risque de rejet sur résistance")
    
    # Candlestick patterns (Weight: 1)
    candles = indicators.get("candlesticks", {})
    candle_signal = candles.get("signal", "neutral")
    candle_pattern = candles.get("pattern", "")
    if candle_signal in ["bullish", "bullish_reversal"]:
        score += 1.5
        pattern_name = candle_pattern.replace("_", " ").title()
        reasons.append(f"📊 Pattern: {pattern_name} - Signal haussier")
    elif candle_signal in ["bearish", "bearish_reversal"]:
        score -= 1.5
        pattern_name = candle_pattern.replace("_", " ").title()
        reasons.append(f"📊 Pattern: {pattern_name} - Signal baissier")
    
    # Volume analysis from market data
    if market_data:
        vol_change = market_data.get("total_volume_change_24h", 0)
        if vol_change > 50:
            score += 0.5
            reasons.append(f"📈 Volume en hausse de {vol_change:.0f}% - Intérêt croissant")
        elif vol_change < -30:
            risk_factors.append("Volume en baisse - Prudence sur la force du mouvement")
    
    # Generate entry/exit levels
    entry_price = current_price or sr.get("current", 0)
    
    # Calculate Stop Loss and Take Profits based on support/resistance and volatility
    if score >= 2:  # Buy signal
        stop_loss = min(support * 0.98, entry_price * 0.95) if support else entry_price * 0.95
        take_profit_1 = entry_price * 1.05  # 5% gain
        take_profit_2 = min(resistance * 0.98, entry_price * 1.12) if resistance else entry_price * 1.12
    elif score <= -2:  # Sell signal
        stop_loss = max(resistance * 1.02, entry_price * 1.05) if resistance else entry_price * 1.05
        take_profit_1 = entry_price * 0.95  # 5% gain on short
        take_profit_2 = max(support * 1.02, entry_price * 0.88) if support else entry_price * 0.88
    else:
        stop_loss = entry_price * 0.95
        take_profit_1 = entry_price * 1.05
        take_profit_2 = entry_price * 1.10
    
    # Risk/Reward calculation
    if score >= 2:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit_1 - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
    elif score <= -2:
        risk = abs(stop_loss - entry_price)
        reward = abs(entry_price - take_profit_1)
        risk_reward = reward / risk if risk > 0 else 0
    else:
        risk_reward = 0
    
    # Generate final recommendation
    if score >= 5:
        action = "STRONG_BUY"
        confidence = "high"
        message = "🟢🟢 ACHAT FORT - Excellente opportunité!"
    elif score >= 3:
        action = "BUY"
        confidence = "high"
        message = "🟢 ACHAT recommandé - Signal fort"
    elif score >= 2:
        action = "BUY"
        confidence = "medium"
        message = "🟢 ACHAT possible - Signal modéré"
    elif score <= -5:
        action = "STRONG_SELL"
        confidence = "high"
        message = "🔴🔴 VENTE FORTE - Signal de sortie!"
    elif score <= -3:
        action = "SELL"
        confidence = "high"
        message = "🔴 VENTE recommandée - Signal fort"
    elif score <= -2:
        action = "SELL"
        confidence = "medium"
        message = "🔴 VENTE possible - Signal modéré"
    else:
        action = "WAIT"
        confidence = "low"
        message = "🟡 ATTENDRE - Pas de signal clair"
    
    return {
        "action": action,
        "confidence": confidence,
        "message": message,
        "score": round(score, 1),
        "reasons": reasons,
        "risk_factors": risk_factors,
        "levels": {
            "entry": round(entry_price, 6) if entry_price < 1 else round(entry_price, 2),
            "stop_loss": round(stop_loss, 6) if stop_loss < 1 else round(stop_loss, 2),
            "take_profit_1": round(take_profit_1, 6) if take_profit_1 < 1 else round(take_profit_1, 2),
            "take_profit_2": round(take_profit_2, 6) if take_profit_2 < 1 else round(take_profit_2, 2)
        },
        "risk_reward_ratio": round(risk_reward, 2)
    }

class TradingAnalysisRequest(BaseModel):
    coin_id: str
    timeframe: str = "4h"  # 1h, 4h, daily
    trading_style: str = "swing"  # scalping, intraday, swing

@api_router.post("/trading/analyze")
async def analyze_for_trading(request: TradingAnalysisRequest, current_user: dict = Depends(get_current_user)):
    """
    Deep technical analysis for trading decisions.
    Uses CryptoCompare as primary (most reliable), with CoinGecko as fallback.
    """
    coin_id = request.coin_id
    timeframe = request.timeframe
    trading_style = request.trading_style
    
    # Get crypto symbol from coin_id
    crypto_symbol = None
    if coin_id in CRYPTO_MAPPING:
        crypto_symbol = CRYPTO_MAPPING[coin_id]["binance_symbol"]
    else:
        # Try to extract symbol from coin_id
        crypto_symbol = coin_id.upper()[:4]
    
    # Map timeframe to CryptoCompare parameters
    timeframe_map = {
        "1h": ("histohour", 168),    # 7 days of hourly data
        "4h": ("histohour", 168),    # Same but we'll aggregate
        "daily": ("histoday", 30)    # 30 days of daily data
    }
    api_type, limit = timeframe_map.get(timeframe, ("histohour", 168))
    
    prices = None
    market_data = {}
    
    try:
        async with httpx.AsyncClient() as client:
            # Strategy 1: Try CryptoCompare first (most reliable)
            try:
                response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/{api_type}",
                    params={
                        "fsym": crypto_symbol,
                        "tsym": "USD",
                        "limit": limit
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("Response") == "Success" and "Data" in data:
                        # Data is directly an array in CryptoCompare response
                        hist_data = data["Data"]
                        if isinstance(hist_data, list) and len(hist_data) > 10:
                            prices = [float(d["close"]) for d in hist_data if d.get("close")]
                            logger.info(f"✅ Trading analyze: Got {len(prices)} prices from CryptoCompare for {coin_id}")
                            
                            # Get current price info
                            latest = hist_data[-1]
                            market_data = {
                                "current_price": {"usd": latest.get("close", prices[-1])},
                                "high_24h": {"usd": latest.get("high", 0)},
                                "low_24h": {"usd": latest.get("low", 0)},
                                "price_change_percentage_24h": 0,
                                "total_volume": {"usd": latest.get("volumeto", 0)}
                            }
            except Exception as e:
                logger.warning(f"Trading analyze: CryptoCompare error for {coin_id}: {e}")
            
            # Strategy 2: Fallback to CoinGecko if CryptoCompare failed
            if not prices or len(prices) < 10:
                days_map = {"1h": 1, "4h": 7, "daily": 30}
                days = days_map.get(timeframe, 7)
                
                for attempt in range(2):
                    try:
                        response = await client.get(
                            f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                            params={"vs_currency": "usd", "days": days},
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            prices = [p[1] for p in data.get("prices", [])]
                            logger.info(f"✅ Trading analyze: Got {len(prices)} prices from CoinGecko for {coin_id}")
                            break
                        elif response.status_code == 429:
                            logger.warning(f"Trading analyze: CoinGecko rate limited, attempt {attempt + 1}/2")
                            if attempt < 1:
                                await asyncio.sleep(2)
                            continue
                    except Exception as e:
                        logger.warning(f"Trading analyze: CoinGecko error attempt {attempt + 1}: {e}")
                        if attempt < 1:
                            await asyncio.sleep(1)
                        continue
            
            if not prices or len(prices) < 10:
                raise HTTPException(
                    status_code=503, 
                    detail="Impossible de récupérer les données historiques. Réessayez dans 30 secondes."
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching data for trading analysis: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données. Réessayez.")
    
    # Calculate all indicators
    indicators = {
        "rsi": calculate_rsi(prices),
        "macd": calculate_macd(prices),
        "bollinger": calculate_bollinger_bands(prices),
        "moving_averages": calculate_moving_averages(prices),
        "support_resistance": calculate_support_resistance(prices),
        "candlesticks": analyze_candlestick_patterns(prices)
    }
    
    # Generate algorithmic recommendation with levels
    algo_recommendation = generate_trading_recommendation(indicators, current_price=prices[-1], market_data=market_data)
    
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
        
        user_msg = UserMessage(text=ai_context)
        ai_response = await chat.send_message(user_msg)
        ai_analysis = str(ai_response) if ai_response else "Analyse non disponible"
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
        except Exception:
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
            market_context += """

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
                except Exception:
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

@api_router.get("/paper-trading/stats")
async def get_paper_trading_stats(current_user: dict = Depends(get_current_user)):
    """Get comprehensive paper trading statistics"""
    trades = await db.paper_trades.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    user = await db.users.find_one({"id": current_user["id"]})
    current_balance = user.get("paper_balance", 10000.0)
    portfolio = user.get("portfolio", {})
    initial_balance = 10000.0
    
    if not trades:
        return {
            "total_trades": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "total_volume": 0,
            "current_balance": current_balance,
            "initial_balance": initial_balance,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "portfolio_value": current_balance,
            "best_trade": None,
            "worst_trade": None,
            "most_traded": None,
            "trading_history": [],
            "daily_pnl": []
        }
    
    total_trades = len(trades)
    buy_trades = len([t for t in trades if t["type"] == "buy"])
    sell_trades = len([t for t in trades if t["type"] == "sell"])
    total_volume = sum(t["amount"] * t["price"] for t in trades)
    
    # Calculate realized P&L from sell trades
    realized_pnl = 0
    trade_pnls = []
    
    # Group trades by symbol
    from collections import defaultdict
    trades_by_symbol = defaultdict(list)
    for t in sorted(trades, key=lambda x: x.get("timestamp", "")):
        trades_by_symbol[t["symbol"]].append(t)
    
    # Calculate P&L for each closed position
    for symbol, symbol_trades in trades_by_symbol.items():
        position_cost = 0
        position_amount = 0
        
        for t in symbol_trades:
            if t["type"] == "buy":
                cost = t["amount"] * t["price"]
                position_cost += cost
                position_amount += t["amount"]
            elif t["type"] == "sell":
                if position_amount > 0:
                    avg_cost = position_cost / position_amount
                    sell_value = t["amount"] * t["price"]
                    cost_basis = t["amount"] * avg_cost
                    pnl = sell_value - cost_basis
                    pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    realized_pnl += pnl
                    trade_pnls.append({
                        "symbol": symbol,
                        "pnl": pnl,
                        "pnl_percent": pnl_percent,
                        "timestamp": t.get("timestamp")
                    })
                    
                    # Update position
                    position_cost -= t["amount"] * avg_cost
                    position_amount -= t["amount"]
    
    # Get current portfolio value with live prices (estimate)
    portfolio_value = current_balance
    for symbol, holding in portfolio.items():
        # Use stored average price as estimate
        portfolio_value += holding.get("amount", 0) * holding.get("avg_price", 0)
    
    total_pnl = portfolio_value - initial_balance
    total_pnl_percent = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
    
    # Best and worst trades
    best_trade = None
    worst_trade = None
    if trade_pnls:
        sorted_pnls = sorted(trade_pnls, key=lambda x: x["pnl"], reverse=True)
        if sorted_pnls:
            best = sorted_pnls[0]
            best_trade = {"symbol": best["symbol"], "pnl": round(best["pnl"], 2), "pnl_percent": round(best["pnl_percent"], 2)}
            worst = sorted_pnls[-1]
            worst_trade = {"symbol": worst["symbol"], "pnl": round(worst["pnl"], 2), "pnl_percent": round(worst["pnl_percent"], 2)}
    
    # Most traded symbol
    symbol_counts = {}
    for t in trades:
        sym = t["symbol"]
        symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
    most_traded = max(symbol_counts.items(), key=lambda x: x[1])[0] if symbol_counts else None
    
    # Recent trading history (last 10)
    trading_history = []
    for t in sorted(trades, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]:
        trading_history.append({
            "symbol": t["symbol"],
            "type": t["type"],
            "amount": t["amount"],
            "price": t["price"],
            "value": round(t["amount"] * t["price"], 2),
            "timestamp": t.get("timestamp", "")[:10] if t.get("timestamp") else ""
        })
    
    # Daily P&L (simplified - based on trade dates)
    daily_pnl = []
    daily_trades = defaultdict(lambda: {"buys": 0, "sells": 0, "volume": 0})
    for t in trades:
        date = t.get("timestamp", "")[:10] if t.get("timestamp") else "unknown"
        daily_trades[date]["volume"] += t["amount"] * t["price"]
        if t["type"] == "buy":
            daily_trades[date]["buys"] += 1
        else:
            daily_trades[date]["sells"] += 1
    
    for date, data in sorted(daily_trades.items(), reverse=True)[:7]:
        daily_pnl.append({
            "date": date,
            "trades": data["buys"] + data["sells"],
            "volume": round(data["volume"], 2)
        })
    
    return {
        "total_trades": total_trades,
        "buy_trades": buy_trades,
        "sell_trades": sell_trades,
        "total_volume": round(total_volume, 2),
        "current_balance": round(current_balance, 2),
        "initial_balance": initial_balance,
        "realized_pnl": round(realized_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percent": round(total_pnl_percent, 2),
        "portfolio_value": round(portfolio_value, 2),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "most_traded": most_traded,
        "trading_history": trading_history,
        "daily_pnl": daily_pnl
    }

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

# ============== ONBOARDING ROUTES ==============

@api_router.post("/onboarding/complete")
async def complete_onboarding(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    """Complete the onboarding process and save user preferences"""
    
    # Map experience level to trading level
    level_map = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "confirmed": "advanced",
        "expert": "advanced"
    }
    trading_level = level_map.get(data.experience_level, "beginner")
    
    # Build preferences object
    preferences = {
        "experience_level": data.experience_level,
        "preferred_markets": data.preferred_markets,
        "trading_goals": data.trading_goals,
        "favorite_assets": data.favorite_assets,
        "onboarding_date": datetime.now(timezone.utc).isoformat()
    }
    
    # Build initial watchlist from favorite cryptos
    watchlist = []
    if "crypto" in data.preferred_markets and data.favorite_assets.get("crypto"):
        watchlist = data.favorite_assets["crypto"][:5]  # Max 5 initial
    
    # Update user
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$set": {
                "trading_level": trading_level,
                "onboarding_completed": True,
                "preferences": preferences,
                "watchlist": watchlist if watchlist else current_user.get("watchlist", [])
            }
        }
    )
    
    # Get updated user
    updated_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "password": 0})
    
    return {
        "success": True,
        "message": "Onboarding completed successfully",
        "user": updated_user
    }

@api_router.get("/onboarding/status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """Check if user has completed onboarding"""
    return {
        "onboarding_completed": current_user.get("onboarding_completed", False),
        "preferences": current_user.get("preferences", None)
    }

@api_router.get("/onboarding/options")
async def get_onboarding_options():
    """Get all available options for onboarding"""
    return {
        "experience_levels": [
            {"id": "beginner", "name": "Débutant", "icon": "🌱", "description": "Je découvre le trading"},
            {"id": "intermediate", "name": "Intermédiaire", "icon": "📈", "description": "Je connais les bases"},
            {"id": "confirmed", "name": "Confirmé", "icon": "🎯", "description": "Je trade régulièrement"},
            {"id": "expert", "name": "Expert", "icon": "👑", "description": "Le trading est mon métier"}
        ],
        "markets": [
            {"id": "crypto", "name": "Cryptomonnaies", "icon": "🪙", "description": "Bitcoin, Ethereum, Altcoins..."},
            {"id": "forex", "name": "Forex", "icon": "💱", "description": "EUR/USD, GBP/USD, USD/JPY..."},
            {"id": "stocks", "name": "Actions", "icon": "📊", "description": "Apple, Tesla, Amazon..."},
            {"id": "indices", "name": "Indices", "icon": "📈", "description": "NASDAQ, S&P 500, CAC 40..."},
            {"id": "commodities", "name": "Matières Premières", "icon": "🥇", "description": "Or, Argent, Pétrole..."},
            {"id": "defi", "name": "DeFi", "icon": "🔗", "description": "Finance décentralisée (bientôt)"}
        ],
        "goals": [
            {"id": "learn", "name": "Apprendre", "icon": "📚", "description": "Comprendre le trading"},
            {"id": "speculate", "name": "Spéculer", "icon": "💰", "description": "Profits court terme"},
            {"id": "invest", "name": "Investir", "icon": "🏦", "description": "Long terme, épargne"},
            {"id": "automate", "name": "Automatiser", "icon": "🤖", "description": "Signaux et alertes IA"},
            {"id": "analyze", "name": "Analyser", "icon": "🔬", "description": "Outils d'analyse technique"}
        ],
        "assets": {
            "crypto": [
                {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "icon": "₿"},
                {"id": "ethereum", "name": "Ethereum", "symbol": "ETH", "icon": "Ξ"},
                {"id": "solana", "name": "Solana", "symbol": "SOL", "icon": "◎"},
                {"id": "ripple", "name": "XRP", "symbol": "XRP", "icon": "✕"},
                {"id": "binancecoin", "name": "BNB", "symbol": "BNB", "icon": "⬡"},
                {"id": "cardano", "name": "Cardano", "symbol": "ADA", "icon": "₳"},
                {"id": "dogecoin", "name": "Dogecoin", "symbol": "DOGE", "icon": "Ð"},
                {"id": "polkadot", "name": "Polkadot", "symbol": "DOT", "icon": "●"},
                {"id": "avalanche-2", "name": "Avalanche", "symbol": "AVAX", "icon": "🔺"},
                {"id": "chainlink", "name": "Chainlink", "symbol": "LINK", "icon": "⬡"}
            ],
            "forex": [
                {"id": "EUR/USD", "name": "Euro / Dollar", "symbol": "EUR/USD"},
                {"id": "GBP/USD", "name": "Livre / Dollar", "symbol": "GBP/USD"},
                {"id": "USD/JPY", "name": "Dollar / Yen", "symbol": "USD/JPY"},
                {"id": "USD/CHF", "name": "Dollar / Franc Suisse", "symbol": "USD/CHF"},
                {"id": "AUD/USD", "name": "Dollar Australien / Dollar", "symbol": "AUD/USD"},
                {"id": "USD/CAD", "name": "Dollar / Dollar Canadien", "symbol": "USD/CAD"}
            ],
            "stocks": [
                {"id": "AAPL", "name": "Apple", "symbol": "AAPL"},
                {"id": "TSLA", "name": "Tesla", "symbol": "TSLA"},
                {"id": "AMZN", "name": "Amazon", "symbol": "AMZN"},
                {"id": "GOOGL", "name": "Google", "symbol": "GOOGL"},
                {"id": "MSFT", "name": "Microsoft", "symbol": "MSFT"},
                {"id": "NVDA", "name": "NVIDIA", "symbol": "NVDA"},
                {"id": "META", "name": "Meta", "symbol": "META"}
            ],
            "indices": [
                {"id": "NASDAQ", "name": "NASDAQ 100", "symbol": "NDX"},
                {"id": "SP500", "name": "S&P 500", "symbol": "SPX"},
                {"id": "DOW", "name": "Dow Jones", "symbol": "DJI"},
                {"id": "CAC40", "name": "CAC 40", "symbol": "CAC"},
                {"id": "DAX", "name": "DAX 40", "symbol": "DAX"},
                {"id": "FTSE", "name": "FTSE 100", "symbol": "FTSE"}
            ],
            "commodities": [
                {"id": "XAU", "name": "Or", "symbol": "XAU/USD", "icon": "🥇"},
                {"id": "XAG", "name": "Argent", "symbol": "XAG/USD", "icon": "🥈"},
                {"id": "WTI", "name": "Pétrole WTI", "symbol": "WTI", "icon": "🛢️"},
                {"id": "BRENT", "name": "Pétrole Brent", "symbol": "BRENT", "icon": "🛢️"},
                {"id": "NG", "name": "Gaz Naturel", "symbol": "NG", "icon": "🔥"},
                {"id": "COPPER", "name": "Cuivre", "symbol": "HG", "icon": "🔶"}
            ]
        }
    }

# ============== SMART INVEST ==============

class SmartInvestRequest(BaseModel):
    investment_amount: float
    include_stocks: bool = True  # Include stocks/indices analysis

class SmartInvestExecute(BaseModel):
    coin_id: str  # Can be crypto id or stock symbol
    asset_type: str = "crypto"  # crypto or stock
    amount_usd: float
    entry_price: float

# Stock/Index symbols for Smart Invest analysis
SMART_INVEST_STOCKS = [
    {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "type": "index"},
    {"symbol": "SPY", "name": "S&P 500 ETF", "type": "index"},
    {"symbol": "AAPL", "name": "Apple", "type": "stock"},
    {"symbol": "MSFT", "name": "Microsoft", "type": "stock"},
    {"symbol": "GOOGL", "name": "Google", "type": "stock"},
    {"symbol": "TSLA", "name": "Tesla", "type": "stock"},
    {"symbol": "NVDA", "name": "NVIDIA", "type": "stock"},
    {"symbol": "AMZN", "name": "Amazon", "type": "stock"},
]

async def analyze_stock_opportunity(client, symbol: str, name: str, stock_type: str, investment_amount: float):
    """Analyze a stock/index using Alpha Vantage data"""
    try:
        # Get daily data
        response = await client.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_API_KEY
            },
            timeout=15.0
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            return None
        
        time_series = data["Time Series (Daily)"]
        dates = sorted(time_series.keys(), reverse=True)[:30]
        
        if len(dates) < 14:
            return None
        
        # Extract prices
        prices = [float(time_series[d]["4. close"]) for d in reversed(dates)]
        volumes = [float(time_series[d]["5. volume"]) for d in reversed(dates)]
        
        current_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 else current_price
        change_24h = ((current_price - prev_price) / prev_price) * 100
        
        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd = calculate_macd(prices)
        bb = calculate_bollinger_bands(prices)
        ma = calculate_moving_averages(prices)
        sr = calculate_support_resistance(prices)
        
        # Calculate score
        score = 0
        reasons = []
        
        # RSI Analysis
        if rsi < 25:
            score += 4
            reasons.append(f"🔥 RSI extrême ({rsi:.1f}) - Excellente opportunité")
        elif rsi < 30:
            score += 3
            reasons.append(f"RSI en survente ({rsi:.1f}) - Signal d'achat fort")
        elif rsi < 40:
            score += 2
            reasons.append(f"RSI favorable ({rsi:.1f}) - Potentiel de rebond")
        elif rsi > 70:
            score -= 3
            reasons.append(f"RSI en surachat ({rsi:.1f})")
        
        # Bollinger Analysis
        if bb.get("position") == "oversold":
            score += 3
            reasons.append("💰 Prix sur bande inférieure Bollinger")
        elif bb.get("position") == "lower_half":
            score += 1
        elif bb.get("position") == "overbought":
            score -= 2
        
        # Trend Analysis
        trend = ma.get("trend", "neutral")
        if trend == "strong_bullish":
            score += 3
            reasons.append("🚀 Tendance fortement haussière")
        elif trend == "bullish":
            score += 2
            reasons.append("📈 Tendance haussière")
        elif trend == "strong_bearish":
            score -= 3
        elif trend == "bearish":
            score -= 2
        
        # MACD Analysis
        if macd.get("trend") == "bullish":
            score += 1.5
            reasons.append("MACD haussier")
        elif macd.get("trend") == "bearish":
            score -= 1.5
        
        # Volume bonus
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[-1]
        if volumes[-1] > avg_volume * 1.5:
            score += 0.5
            reasons.append("📊 Volume élevé")
        
        # Calculate levels
        support = sr.get("support", current_price * 0.95)
        resistance = sr.get("resistance", current_price * 1.10)
        
        stop_loss = max(support * 0.98, current_price * 0.95)
        take_profit_1 = current_price * 1.05
        take_profit_2 = min(resistance * 0.98, current_price * 1.10)
        
        quantity = investment_amount / current_price
        
        return {
            "coin_id": symbol,
            "name": name,
            "symbol": symbol,
            "asset_type": "stock",
            "stock_type": stock_type,
            "current_price": current_price,
            "change_24h": change_24h,
            "score": round(score, 1),
            "confidence": "HAUTE" if score >= 5 else "MOYENNE" if score >= 3 else "MODÉRÉE",
            "quantity_to_buy": quantity,
            "investment_amount": investment_amount,
            "indicators": {
                "rsi": round(rsi, 1),
                "trend": trend,
                "bollinger": bb.get("position", "middle"),
                "macd": macd.get("trend", "neutral")
            },
            "levels": {
                "entry": current_price,
                "stop_loss": round(stop_loss, 2),
                "take_profit_1": round(take_profit_1, 2),
                "take_profit_2": round(take_profit_2, 2)
            },
            "reasons": reasons
        }
        
    except Exception as e:
        logger.warning(f"Error analyzing stock {symbol}: {e}")
        return None

@api_router.post("/smart-invest/analyze")
async def smart_invest_analyze(request: SmartInvestRequest, current_user: dict = Depends(get_current_user)):
    """
    Analyze the market and recommend the best investment opportunity.
    Uses CryptoCompare as primary (most reliable), with other APIs as fallback.
    Analyzes both crypto AND stocks/indices for the best opportunity.
    """
    if request.investment_amount < 10:
        return {"error": "Montant minimum: 10€"}
    
    watchlist = current_user.get("watchlist", ["bitcoin", "ethereum", "solana", "ripple", "cardano"])
    
    if not watchlist:
        watchlist = ["bitcoin", "ethereum", "solana"]
    
    best_opportunity = None
    best_score = -999
    all_opportunities = []
    
    try:
        async with httpx.AsyncClient() as client:
            # ============== GET CURRENT PRICES FROM CRYPTOCOMPARE ==============
            logger.info("Smart Invest: Fetching data from CryptoCompare...")
            
            # Build symbol list
            symbols = []
            for coin_id in watchlist[:10]:
                if coin_id in CRYPTO_MAPPING:
                    symbols.append(CRYPTO_MAPPING[coin_id]["binance_symbol"])
            
            if not symbols:
                symbols = ["BTC", "ETH", "SOL", "XRP", "ADA"]
            
            symbols_str = ",".join(symbols)
            
            # Get current prices
            price_data = {}
            try:
                price_response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/pricemultifull",
                    params={"fsyms": symbols_str, "tsyms": "USD"},
                    timeout=15.0
                )
                if price_response.status_code == 200:
                    data = price_response.json()
                    if "RAW" in data:
                        price_data = data["RAW"]
                        logger.info(f"✅ Smart Invest: Got prices for {len(price_data)} cryptos from CryptoCompare")
            except Exception as e:
                logger.warning(f"Smart Invest: CryptoCompare price error: {e}")
            
            if not price_data:
                return {"error": "Impossible de récupérer les prix. Réessayez dans 30 secondes."}
            
            analyzed_count = 0
            
            # Analyze each coin
            for coin_id in watchlist[:8]:
                try:
                    # Get coin info from mapping
                    if coin_id not in CRYPTO_MAPPING:
                        continue
                    
                    coin_info = CRYPTO_MAPPING[coin_id]
                    crypto_symbol = coin_info["binance_symbol"]
                    
                    # Get current price from CryptoCompare
                    if crypto_symbol not in price_data or "USD" not in price_data[crypto_symbol]:
                        continue
                    
                    usd_data = price_data[crypto_symbol]["USD"]
                    current_price = usd_data.get("PRICE", 0)
                    change_24h = usd_data.get("CHANGEPCT24HOUR", 0)
                    
                    if current_price <= 0:
                        continue
                    
                    # Get historical data from CryptoCompare
                    hist_response = await client.get(
                        f"{CRYPTOCOMPARE_API_URL}/histohour",
                        params={
                            "fsym": crypto_symbol,
                            "tsym": "USD",
                            "limit": 84  # ~3.5 days of hourly data
                        },
                        timeout=10.0
                    )
                    
                    if hist_response.status_code != 200:
                        continue
                    
                    hist_data = hist_response.json()
                    if hist_data.get("Response") != "Success" or "Data" not in hist_data:
                        continue
                    
                    data_points = hist_data["Data"].get("Data", hist_data.get("Data", []))
                    if not data_points or len(data_points) < 30:
                        continue
                    
                    prices = [float(d["close"]) for d in data_points if d.get("close")]
                    
                    if len(prices) < 30:
                        continue
                    
                    # Calculate indicators
                    rsi = calculate_rsi(prices)
                    macd = calculate_macd(prices)
                    bb = calculate_bollinger_bands(prices)
                    ma = calculate_moving_averages(prices)
                    sr = calculate_support_resistance(prices)
                    
                    # Use Binance data for current price (already set above)
                    # current_price and change_24h are from Binance ticker
                    
                    # Calculate composite score
                    score = 0
                    reasons = []
                    
                    # RSI Analysis (weight: 3)
                    if rsi < 25:
                        score += 4
                        reasons.append(f"🔥 RSI extrême ({rsi:.1f}) - Excellente opportunité d'achat")
                    elif rsi < 30:
                        score += 3
                        reasons.append(f"RSI en survente ({rsi:.1f}) - Signal d'achat fort")
                    elif rsi < 40:
                        score += 2
                        reasons.append(f"RSI favorable ({rsi:.1f}) - Potentiel de rebond")
                    elif rsi > 70:
                        score -= 3
                        reasons.append(f"RSI en surachat ({rsi:.1f}) - Éviter")
                    
                    # Bollinger Analysis (weight: 2)
                    if bb.get("position") == "oversold":
                        score += 3
                        reasons.append("💰 Prix sur bande inférieure Bollinger - Zone d'achat optimale")
                    elif bb.get("position") == "lower_half":
                        score += 1
                    elif bb.get("position") == "overbought":
                        score -= 2
                    
                    # Trend Analysis (weight: 2)
                    trend = ma.get("trend", "neutral")
                    if trend == "strong_bullish":
                        score += 3
                        reasons.append("🚀 Tendance fortement haussière")
                    elif trend == "bullish":
                        score += 2
                        reasons.append("📈 Tendance haussière confirmée")
                    elif trend == "strong_bearish":
                        score -= 3
                    elif trend == "bearish":
                        score -= 2
                    
                    # MACD Analysis (weight: 1)
                    if macd.get("trend") == "bullish":
                        score += 1.5
                        reasons.append("MACD haussier - Momentum positif")
                    elif macd.get("trend") == "bearish":
                        score -= 1.5
                    
                    # 24h change bonus (small weight)
                    if -10 < change_24h < -3:
                        score += 1
                        reasons.append(f"Correction récente ({change_24h:.1f}%) - Point d'entrée potentiel")
                    elif change_24h > 15:
                        score -= 1
                    
                    # Calculate entry/exit levels
                    support = sr.get("support", current_price * 0.95)
                    resistance = sr.get("resistance", current_price * 1.15)
                    
                    stop_loss = max(support * 0.98, current_price * 0.92)
                    take_profit_1 = current_price * 1.08
                    take_profit_2 = min(resistance * 0.98, current_price * 1.15)
                    
                    # Use CRYPTO_MAPPING for names
                    coin_name = coin_info["name"]
                    coin_symbol = coin_info["binance_symbol"]
                    
                    # Check if this is the best crypto opportunity
                    if score >= 2:
                        quantity = request.investment_amount / current_price
                        
                        crypto_opportunity = {
                            "coin_id": coin_id,
                            "name": coin_name,
                            "symbol": coin_symbol,
                            "asset_type": "crypto",
                            "current_price": current_price,
                            "change_24h": change_24h,
                            "score": round(score, 1),
                            "confidence": "HAUTE" if score >= 5 else "MOYENNE" if score >= 3 else "MODÉRÉE",
                            "quantity_to_buy": quantity,
                            "investment_amount": request.investment_amount,
                            "indicators": {
                                "rsi": round(rsi, 1),
                                "trend": trend,
                                "bollinger": bb.get("position", "middle"),
                                "macd": macd.get("trend", "neutral")
                            },
                            "levels": {
                                "entry": current_price,
                                "stop_loss": round(stop_loss, 2 if stop_loss >= 1 else 6),
                                "take_profit_1": round(take_profit_1, 2 if take_profit_1 >= 1 else 6),
                                "take_profit_2": round(take_profit_2, 2 if take_profit_2 >= 1 else 6)
                            },
                            "reasons": reasons,
                            "source": "binance"
                        }
                        all_opportunities.append(crypto_opportunity)
                        
                        if score > best_score:
                            best_score = score
                            best_opportunity = crypto_opportunity
                    
                    analyzed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error analyzing {coin_id}: {e}")
                    continue
            
            # ============== ANALYZE STOCKS/INDICES ==============
            if request.include_stocks and ALPHA_VANTAGE_API_KEY:
                logger.info("Smart Invest: Analyzing stocks and indices...")
                
                for stock_info in SMART_INVEST_STOCKS[:4]:  # Limit to avoid rate limits
                    await asyncio.sleep(0.3)  # Alpha Vantage rate limit
                    
                    stock_result = await analyze_stock_opportunity(
                        client,
                        stock_info["symbol"],
                        stock_info["name"],
                        stock_info["type"],
                        request.investment_amount
                    )
                    
                    if stock_result and stock_result["score"] >= 2:
                        all_opportunities.append(stock_result)
                        
                        if stock_result["score"] > best_score:
                            best_score = stock_result["score"]
                            best_opportunity = stock_result
                        
                        analyzed_count += 1
            
            if not best_opportunity:
                if analyzed_count == 0:
                    return {
                        "error": "Impossible d'analyser les actifs. Les APIs sont surchargées. Réessayez dans 1 minute.",
                        "message": "L'IA n'a pas pu récupérer les données de marché."
                    }
                return {
                    "error": "Aucune opportunité détectée. Les marchés sont neutres ou en surachat. Réessayez plus tard.",
                    "message": "BULL recommande d'attendre une meilleure opportunité."
                }
            
            # Add info about other opportunities
            best_opportunity["other_opportunities"] = [
                {"name": o["name"], "symbol": o["symbol"], "score": o["score"], "asset_type": o.get("asset_type", "crypto")}
                for o in sorted(all_opportunities, key=lambda x: x["score"], reverse=True)[:5]
                if o["coin_id"] != best_opportunity["coin_id"]
            ]
            
            return best_opportunity
            
    except Exception as e:
        logger.error(f"Smart invest analysis error: {e}")
        return {"error": f"Erreur d'analyse: {str(e)}"}

@api_router.post("/smart-invest/execute")
async def smart_invest_execute(request: SmartInvestExecute, current_user: dict = Depends(get_current_user)):
    """
    Execute a smart investment as a paper trade.
    """
    user_id = current_user["id"]
    
    # Get user's paper trading balance
    user = await db.users.find_one({"id": user_id})
    balance = user.get("paper_balance", 10000.0)
    portfolio = user.get("portfolio", {})
    
    if request.amount_usd > balance:
        return {"success": False, "error": "Solde insuffisant en Paper Trading"}
    
    # Calculate quantity
    quantity = request.amount_usd / request.entry_price
    
    # Update portfolio
    current_holding = portfolio.get(request.coin_id, {"amount": 0, "avg_price": 0})
    total_amount = current_holding["amount"] + quantity
    
    if total_amount > 0:
        new_avg_price = ((current_holding["amount"] * current_holding["avg_price"]) + request.amount_usd) / total_amount
    else:
        new_avg_price = request.entry_price
    
    portfolio[request.coin_id] = {"amount": total_amount, "avg_price": new_avg_price}
    new_balance = balance - request.amount_usd
    
    # Update user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"paper_balance": new_balance, "portfolio": portfolio}}
    )
    
    # Record the trade
    trade_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "symbol": request.coin_id,
        "type": "buy",
        "amount": quantity,
        "price": request.entry_price,
        "total_value": request.amount_usd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "executed",
        "source": "smart_invest"
    }
    await db.paper_trades.insert_one(trade_doc)
    
    return {
        "success": True,
        "message": "Investissement exécuté avec succès!",
        "trade_id": trade_doc["id"],
        "coin_id": request.coin_id,
        "quantity": quantity,
        "entry_price": request.entry_price,
        "total_invested": request.amount_usd,
        "new_balance": new_balance
    }

# ============== SIMPLE BACKTESTING ==============

@api_router.post("/trading/backtest")
async def simple_backtest(
    coin_id: str,
    strategy: str = "rsi_oversold",
    days: int = 30,
    initial_capital: float = 10000,
    current_user: dict = Depends(get_current_user)
):
    """
    Simple backtesting of trading strategies.
    Strategies: rsi_oversold, rsi_overbought, ma_crossover, bollinger_bounce
    """
    if days > 365:
        days = 365
    
    try:
        async with httpx.AsyncClient() as client:
            # Get historical data
            response = await client.get(
                f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                params={"vs_currency": "usd", "days": days},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return {"error": "Impossible de récupérer les données historiques"}
            
            data = response.json()
            prices = [p[1] for p in data.get("prices", [])]
            
            if len(prices) < 50:
                return {"error": "Pas assez de données historiques"}
            
            # Initialize backtesting variables
            capital = initial_capital
            position = 0  # Amount of crypto held
            entry_price = 0
            trades = []
            wins = 0
            losses = 0
            total_pnl = 0
            
            # Strategy implementation
            for i in range(20, len(prices)):
                price = prices[i]
                
                # Calculate indicators for this point
                window = prices[max(0, i-14):i+1]
                rsi = calculate_rsi(window)
                bb = calculate_bollinger_bands(prices[max(0, i-20):i+1])
                
                # Short MA and Long MA for crossover
                ma_short = sum(prices[i-10:i+1]) / 11 if i >= 10 else price
                ma_long = sum(prices[i-20:i+1]) / 21 if i >= 20 else price
                
                buy_signal = False
                sell_signal = False
                
                # Apply strategy rules
                if strategy == "rsi_oversold":
                    buy_signal = rsi < 30 and position == 0
                    sell_signal = rsi > 70 and position > 0
                elif strategy == "rsi_overbought":
                    # Inverse strategy - buy high, sell low (for comparison)
                    buy_signal = rsi > 70 and position == 0
                    sell_signal = rsi < 30 and position > 0
                elif strategy == "ma_crossover":
                    buy_signal = ma_short > ma_long and position == 0
                    sell_signal = ma_short < ma_long and position > 0
                elif strategy == "bollinger_bounce":
                    buy_signal = bb.get("position") == "oversold" and position == 0
                    sell_signal = bb.get("position") == "overbought" and position > 0
                
                # Execute trades
                if buy_signal and capital > 0:
                    # Buy with all capital
                    position = capital / price
                    entry_price = price
                    capital = 0
                    trades.append({
                        "type": "buy",
                        "price": round(price, 2),
                        "amount": round(position, 6),
                        "day": i
                    })
                elif sell_signal and position > 0:
                    # Sell all
                    exit_value = position * price
                    pnl = exit_value - (position * entry_price)
                    pnl_percent = (price - entry_price) / entry_price * 100
                    
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                    
                    total_pnl += pnl
                    capital = exit_value
                    
                    trades.append({
                        "type": "sell",
                        "price": round(price, 2),
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_percent, 2),
                        "day": i
                    })
                    position = 0
            
            # Close any open position at the end
            final_value = capital
            if position > 0:
                final_value = position * prices[-1]
                pnl = final_value - (position * entry_price)
                if pnl > 0:
                    wins += 1
                else:
                    losses += 1
                total_pnl += pnl
            
            # Calculate statistics
            total_trades = len([t for t in trades if t["type"] == "sell"])
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            total_return = ((final_value - initial_capital) / initial_capital * 100)
            
            # Buy & Hold comparison
            buy_hold_return = ((prices[-1] - prices[20]) / prices[20] * 100)
            
            return {
                "strategy": strategy,
                "coin_id": coin_id,
                "period_days": days,
                "initial_capital": initial_capital,
                "final_value": round(final_value, 2),
                "total_return": round(total_return, 2),
                "total_pnl": round(total_pnl, 2),
                "total_trades": total_trades,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 1),
                "buy_hold_return": round(buy_hold_return, 2),
                "strategy_vs_buyhold": round(total_return - buy_hold_return, 2),
                "trades_sample": trades[-10:] if trades else [],
                "message": f"Stratégie {'gagnante' if total_return > buy_hold_return else 'moins performante'} vs Buy & Hold"
            }
            
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return {"error": f"Erreur de backtesting: {str(e)}"}

# ============== OPPORTUNITY SCANNER ==============

@api_router.get("/trading/scan-opportunities")
async def scan_trading_opportunities(current_user: dict = Depends(get_current_user)):
    """
    Scan user's watchlist for trading opportunities.
    Returns ranked list of assets with buy/sell signals.
    """
    watchlist = current_user.get("watchlist", ["bitcoin", "ethereum", "solana"])
    
    if not watchlist:
        return {"opportunities": [], "message": "Watchlist vide. Ajoutez des actifs à suivre."}
    
    opportunities = []
    
    # Fetch all prices in one call
    try:
        async with httpx.AsyncClient() as client:
            # Get prices for all watchlist items
            response = await client.get(
                f"{COINGECKO_API_URL}/simple/price",
                params={
                    "ids": ",".join(watchlist[:10]),  # Max 10 to avoid rate limits
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true"
                },
                timeout=15.0
            )
            
            if response.status_code != 200:
                return {"opportunities": [], "message": "Erreur API - réessayez dans 1 minute"}
            
            prices_data = response.json()
            
            # Get historical data for each coin to calculate indicators
            for coin_id in watchlist[:5]:  # Limit to 5 to avoid rate limits
                try:
                    # Get 7 days of data for analysis
                    hist_response = await client.get(
                        f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                        params={"vs_currency": "usd", "days": 7},
                        timeout=15.0
                    )
                    
                    if hist_response.status_code != 200:
                        continue
                    
                    hist_data = hist_response.json()
                    prices = [p[1] for p in hist_data.get("prices", [])]
                    
                    if len(prices) < 20:
                        continue
                    
                    # Calculate indicators
                    rsi = calculate_rsi(prices)
                    macd = calculate_macd(prices)
                    bb = calculate_bollinger_bands(prices)
                    ma = calculate_moving_averages(prices)
                    
                    # Calculate opportunity score
                    score = 0
                    signals = []
                    
                    # RSI
                    if rsi < 30:
                        score += 3
                        signals.append(f"RSI survente ({rsi})")
                    elif rsi < 40:
                        score += 1
                        signals.append(f"RSI bas ({rsi})")
                    elif rsi > 70:
                        score -= 3
                        signals.append(f"RSI surachat ({rsi})")
                    
                    # Bollinger
                    if bb.get("position") == "oversold":
                        score += 2
                        signals.append("Sur bande Bollinger inf.")
                    elif bb.get("position") == "overbought":
                        score -= 2
                        signals.append("Sur bande Bollinger sup.")
                    
                    # Trend
                    trend = ma.get("trend", "neutral")
                    if trend in ["strong_bullish", "bullish"]:
                        score += 2
                        signals.append(f"Tendance {trend}")
                    elif trend in ["strong_bearish", "bearish"]:
                        score -= 2
                        signals.append(f"Tendance {trend}")
                    
                    # MACD
                    if macd.get("trend") == "bullish":
                        score += 1
                        signals.append("MACD haussier")
                    elif macd.get("trend") == "bearish":
                        score -= 1
                        signals.append("MACD baissier")
                    
                    current_price = prices[-1]
                    price_24h = prices_data.get(coin_id, {})
                    change_24h = price_24h.get("usd_24h_change", 0)
                    
                    # Determine action
                    if score >= 4:
                        action = "STRONG_BUY"
                        confidence = "high"
                        emoji = "🟢🟢"
                    elif score >= 2:
                        action = "BUY"
                        confidence = "medium"
                        emoji = "🟢"
                    elif score <= -4:
                        action = "STRONG_SELL"
                        confidence = "high"
                        emoji = "🔴🔴"
                    elif score <= -2:
                        action = "SELL"
                        confidence = "medium"
                        emoji = "🔴"
                    else:
                        action = "HOLD"
                        confidence = "low"
                        emoji = "🟡"
                    
                    opportunities.append({
                        "coin_id": coin_id,
                        "name": coin_id.replace("-", " ").title(),
                        "current_price": round(current_price, 2 if current_price >= 1 else 6),
                        "change_24h": round(change_24h, 2) if change_24h else 0,
                        "action": action,
                        "confidence": confidence,
                        "score": score,
                        "emoji": emoji,
                        "signals": signals,
                        "rsi": round(rsi, 1),
                        "trend": trend
                    })
                    
                except Exception as e:
                    logger.warning(f"Error analyzing {coin_id}: {e}")
                    continue
                
    except Exception as e:
        logger.error(f"Error in opportunity scanner: {e}")
        return {"opportunities": [], "message": "Erreur lors du scan - réessayez"}
    
    # Sort by absolute score (best opportunities first)
    opportunities.sort(key=lambda x: abs(x["score"]), reverse=True)
    
    # Generate summary
    buy_signals = len([o for o in opportunities if o["action"] in ["BUY", "STRONG_BUY"]])
    sell_signals = len([o for o in opportunities if o["action"] in ["SELL", "STRONG_SELL"]])
    
    summary = f"🔍 Scan terminé: {buy_signals} signal(s) d'achat, {sell_signals} signal(s) de vente"
    
    return {
        "opportunities": opportunities,
        "summary": summary,
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "watchlist_size": len(watchlist)
    }

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

# ============== ACADEMY ENDPOINTS ==============

from academy_data import ACADEMY_MODULES, BADGES, LEVEL_THRESHOLDS, XP_REWARDS
from academy_data_part2 import ACADEMY_MODULES_PART2, ACADEMY_MODULE_6

# Combine all modules
ALL_ACADEMY_MODULES = ACADEMY_MODULES + ACADEMY_MODULES_PART2 + [ACADEMY_MODULE_6]

def calculate_level(xp: int) -> dict:
    """Calculate level from XP"""
    current_level = LEVEL_THRESHOLDS[0]
    next_level = LEVEL_THRESHOLDS[1] if len(LEVEL_THRESHOLDS) > 1 else None
    
    for i, level in enumerate(LEVEL_THRESHOLDS):
        if xp >= level["min_xp"]:
            current_level = level
            next_level = LEVEL_THRESHOLDS[i + 1] if i + 1 < len(LEVEL_THRESHOLDS) else None
    
    return {
        "level": current_level["level"],
        "title": current_level["title"],
        "icon": current_level["icon"],
        "current_xp": xp,
        "next_level_xp": next_level["min_xp"] if next_level else None,
        "xp_to_next": (next_level["min_xp"] - xp) if next_level else 0
    }

@api_router.get("/academy/modules")
async def get_academy_modules(current_user: dict = Depends(get_current_user)):
    """Get all academy modules with progress"""
    # Get user progress
    progress = await db.academy_progress.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not progress:
        progress = {
            "user_id": current_user["id"],
            "total_xp": 0,
            "completed_lessons": [],
            "completed_quizzes": [],
            "quiz_scores": {},
            "badges": [],
            "streak_days": 0
        }
    
    # Build response with progress
    modules_with_progress = []
    for mod in ALL_ACADEMY_MODULES:
        lesson_ids = [les["id"] for les in mod["lessons"]]
        completed_lessons = [les for les in lesson_ids if les in progress.get("completed_lessons", [])]
        quiz_completed = mod["id"] in progress.get("completed_quizzes", [])
        quiz_score = progress.get("quiz_scores", {}).get(mod["id"], None)
        
        modules_with_progress.append({
            "id": mod["id"],
            "title": mod["title"],
            "description": mod["description"],
            "icon": mod["icon"],
            "color": mod["color"],
            "order": mod["order"],
            "estimated_time": mod["estimated_time"],
            "total_lessons": len(mod["lessons"]),
            "completed_lessons": len(completed_lessons),
            "quiz_completed": quiz_completed,
            "quiz_score": quiz_score,
            "is_locked": mod["order"] > 1 and not any(
                m["id"] in progress.get("completed_quizzes", [])
                for m in ALL_ACADEMY_MODULES if m["order"] == mod["order"] - 1
            )
        })
    
    return {
        "modules": modules_with_progress,
        "user_progress": calculate_level(progress.get("total_xp", 0)),
        "total_xp": progress.get("total_xp", 0),
        "badges": progress.get("badges", []),
        "streak_days": progress.get("streak_days", 0)
    }

@api_router.get("/academy/modules/{module_id}")
async def get_module_detail(module_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed module with all lessons"""
    module = next((m for m in ALL_ACADEMY_MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get user progress
    progress = await db.academy_progress.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    completed_lessons = progress.get("completed_lessons", []) if progress else []
    
    # Add completion status to lessons
    lessons_with_status = []
    for lesson in module["lessons"]:
        lessons_with_status.append({
            **lesson,
            "completed": lesson["id"] in completed_lessons
        })
    
    return {
        **module,
        "lessons": lessons_with_status,
        "quiz_info": {
            "title": module["quiz"]["title"],
            "description": module["quiz"]["description"],
            "passing_score": module["quiz"]["passing_score"],
            "question_count": len(module["quiz"]["questions"])
        }
    }

@api_router.get("/academy/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Get lesson content"""
    for module in ALL_ACADEMY_MODULES:
        for lesson in module["lessons"]:
            if lesson["id"] == lesson_id:
                return {
                    "lesson": lesson,
                    "module_id": module["id"],
                    "module_title": module["title"]
                }
    
    raise HTTPException(status_code=404, detail="Lesson not found")

@api_router.post("/academy/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a lesson as complete and earn XP"""
    # Find the lesson
    lesson = None
    for m in ALL_ACADEMY_MODULES:
        for les in m["lessons"]:
            if les["id"] == lesson_id:
                lesson = les
                break
        if lesson:
            break
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get or create progress
    progress = await db.academy_progress.find_one({"user_id": current_user["id"]})
    
    if not progress:
        progress = {
            "user_id": current_user["id"],
            "total_xp": 0,
            "completed_lessons": [],
            "completed_quizzes": [],
            "quiz_scores": {},
            "badges": [],
            "streak_days": 0,
            "last_activity": None,
            "daily_xp_earned": 0
        }
        await db.academy_progress.insert_one(progress)
    
    xp_earned = 0
    badges_earned = []
    
    # Check if already completed
    if lesson_id not in progress.get("completed_lessons", []):
        xp_earned = lesson["xp_reward"]
        
        # Update progress
        new_completed = progress.get("completed_lessons", []) + [lesson_id]
        new_xp = progress.get("total_xp", 0) + xp_earned
        
        # Check for badges
        if len(new_completed) == 1:
            badges_earned.append("first_lesson")
        if len(new_completed) == 5:
            badges_earned.append("curious_mind")
        if len(new_completed) == 15:
            badges_earned.append("bookworm")
        
        # Update streak
        last_activity = progress.get("last_activity")
        streak = progress.get("streak_days", 0)
        
        if last_activity:
            last_date = datetime.fromisoformat(last_activity.replace('Z', '+00:00')).date()
            today_date = datetime.now(timezone.utc).date()
            if (today_date - last_date).days == 1:
                streak += 1
                xp_earned += XP_REWARDS["daily_streak"]
            elif (today_date - last_date).days > 1:
                streak = 1
        else:
            streak = 1
        
        # Check streak badges
        if streak == 3 and "streak_3" not in progress.get("badges", []):
            badges_earned.append("streak_3")
        if streak == 7 and "streak_7" not in progress.get("badges", []):
            badges_earned.append("streak_7")
        if streak == 30 and "streak_30" not in progress.get("badges", []):
            badges_earned.append("streak_30")
        
        # Save progress
        await db.academy_progress.update_one(
            {"user_id": current_user["id"]},
            {
                "$set": {
                    "completed_lessons": new_completed,
                    "total_xp": new_xp,
                    "streak_days": streak,
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                    "badges": progress.get("badges", []) + badges_earned
                }
            },
            upsert=True
        )
    
    level_info = calculate_level(progress.get("total_xp", 0) + xp_earned)
    
    return {
        "success": True,
        "xp_earned": xp_earned,
        "total_xp": progress.get("total_xp", 0) + xp_earned,
        "badges_earned": badges_earned,
        "level": level_info
    }

@api_router.get("/academy/quiz/{module_id}")
async def get_quiz(module_id: str, current_user: dict = Depends(get_current_user)):
    """Get quiz questions for a module"""
    module = next((m for m in ALL_ACADEMY_MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Return questions without correct answers
    questions = []
    for q in module["quiz"]["questions"]:
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "type": q["type"],
            "options": q["options"]
        })
    
    return {
        "module_id": module_id,
        "title": module["quiz"]["title"],
        "description": module["quiz"]["description"],
        "passing_score": module["quiz"]["passing_score"],
        "questions": questions
    }

@api_router.post("/academy/quiz/{module_id}/submit")
async def submit_quiz(module_id: str, submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    """Submit quiz answers and get results"""
    module = next((m for m in ALL_ACADEMY_MODULES if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    quiz = module["quiz"]
    correct_count = 0
    correct_answers = {}
    explanations = {}
    
    for question in quiz["questions"]:
        q_id = question["id"]
        user_answer = submission.answers.get(q_id)
        is_correct = user_answer == question["correct_answer"]
        correct_answers[q_id] = is_correct
        explanations[q_id] = question["explanation"]
        if is_correct:
            correct_count += 1
    
    total = len(quiz["questions"])
    percentage = (correct_count / total) * 100 if total > 0 else 0
    passed = percentage >= quiz["passing_score"]
    
    # Calculate XP
    xp_earned = 0
    badges_earned = []
    
    # Get user progress
    progress = await db.academy_progress.find_one({"user_id": current_user["id"]})
    if not progress:
        progress = {
            "user_id": current_user["id"],
            "total_xp": 0,
            "completed_lessons": [],
            "completed_quizzes": [],
            "quiz_scores": {},
            "badges": []
        }
    
    # Award XP only if passed and first time
    is_first_time = module_id not in progress.get("completed_quizzes", [])
    
    if passed:
        if is_first_time:
            xp_earned = XP_REWARDS["quiz_pass"]
            if percentage == 100:
                xp_earned += XP_REWARDS["quiz_perfect"]
                if "quiz_master" not in progress.get("badges", []):
                    badges_earned.append("quiz_master")
            
            # Module completion badge
            module_badge = f"module_{module['order']}_complete"
            if module_badge not in progress.get("badges", []):
                badge_map = {
                    1: "module_1_complete",
                    2: "module_2_complete",
                    3: "module_3_complete",
                    4: "module_4_complete",
                    5: "module_5_complete",
                    6: "module_6_complete"
                }
                if module["order"] in badge_map:
                    badges_earned.append(badge_map[module["order"]])
            
            # Add module XP
            xp_earned += XP_REWARDS["module_complete"]
            
            # Check if all modules complete
            new_completed = progress.get("completed_quizzes", []) + [module_id]
            if len(new_completed) == len(ALL_ACADEMY_MODULES):
                xp_earned += XP_REWARDS["all_modules_complete"]
                badges_earned.append("graduate")
        
        # Update progress
        new_quizzes = list(set(progress.get("completed_quizzes", []) + [module_id]))
        new_scores = {**progress.get("quiz_scores", {}), module_id: int(percentage)}
        new_xp = progress.get("total_xp", 0) + xp_earned
        new_badges = list(set(progress.get("badges", []) + badges_earned))
        
        await db.academy_progress.update_one(
            {"user_id": current_user["id"]},
            {
                "$set": {
                    "completed_quizzes": new_quizzes,
                    "quiz_scores": new_scores,
                    "total_xp": new_xp,
                    "badges": new_badges,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    return {
        "score": correct_count,
        "total": total,
        "percentage": round(percentage, 1),
        "passed": passed,
        "passing_score": quiz["passing_score"],
        "xp_earned": xp_earned,
        "badges_earned": badges_earned,
        "correct_answers": correct_answers,
        "explanations": explanations,
        "level": calculate_level(progress.get("total_xp", 0) + xp_earned)
    }

@api_router.get("/academy/progress")
async def get_academy_progress(current_user: dict = Depends(get_current_user)):
    """Get user's academy progress"""
    progress = await db.academy_progress.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not progress:
        progress = {
            "user_id": current_user["id"],
            "total_xp": 0,
            "completed_lessons": [],
            "completed_quizzes": [],
            "quiz_scores": {},
            "badges": [],
            "streak_days": 0
        }
    
    # Calculate stats
    total_lessons = sum(len(m["lessons"]) for m in ALL_ACADEMY_MODULES)
    completed_lessons = len(progress.get("completed_lessons", []))
    total_modules = len(ALL_ACADEMY_MODULES)
    completed_modules = len(progress.get("completed_quizzes", []))
    
    # Get badge details
    badge_details = []
    for badge_id in progress.get("badges", []):
        badge = next((b for b in BADGES if b["id"] == badge_id), None)
        if badge:
            badge_details.append(badge)
    
    return {
        "level": calculate_level(progress.get("total_xp", 0)),
        "total_xp": progress.get("total_xp", 0),
        "streak_days": progress.get("streak_days", 0),
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "completed_modules": completed_modules,
        "total_modules": total_modules,
        "progress_percentage": round((completed_lessons / total_lessons) * 100, 1) if total_lessons > 0 else 0,
        "badges": badge_details,
        "quiz_scores": progress.get("quiz_scores", {})
    }

@api_router.get("/academy/leaderboard")
async def get_leaderboard(current_user: dict = Depends(get_current_user)):
    """Get academy leaderboard"""
    # Get all progress sorted by XP
    all_progress = await db.academy_progress.find(
        {},
        {"_id": 0}
    ).sort("total_xp", -1).limit(20).to_list(20)
    
    leaderboard = []
    for i, prog in enumerate(all_progress):
        user = await db.users.find_one({"id": prog["user_id"]}, {"_id": 0, "password": 0})
        if user:
            level_info = calculate_level(prog.get("total_xp", 0))
            leaderboard.append({
                "rank": i + 1,
                "user_id": user["id"],
                "name": user.get("name", "Trader Anonyme"),
                "total_xp": prog.get("total_xp", 0),
                "level": level_info["level"],
                "level_title": level_info["title"],
                "level_icon": level_info["icon"],
                "badges_count": len(prog.get("badges", [])),
                "is_current_user": user["id"] == current_user["id"]
            })
    
    # Find current user's rank if not in top 20
    current_user_in_list = any(entry["is_current_user"] for entry in leaderboard)
    current_user_rank = None
    
    if not current_user_in_list:
        user_progress = await db.academy_progress.find_one({"user_id": current_user["id"]})
        if user_progress:
            higher_count = await db.academy_progress.count_documents(
                {"total_xp": {"$gt": user_progress.get("total_xp", 0)}}
            )
            current_user_rank = higher_count + 1
    
    return {
        "leaderboard": leaderboard,
        "current_user_rank": current_user_rank
    }

@api_router.get("/academy/badges")
async def get_all_badges(current_user: dict = Depends(get_current_user)):
    """Get all available badges with unlock status"""
    progress = await db.academy_progress.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    earned_badges = progress.get("badges", []) if progress else []
    
    badges_with_status = []
    for badge in BADGES:
        badges_with_status.append({
            **badge,
            "unlocked": badge["id"] in earned_badges
        })
    
    return badges_with_status

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
