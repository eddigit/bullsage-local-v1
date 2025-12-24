from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

# ============== USER MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    trading_level: str = "beginner"

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
    avatar: Optional[str] = None
    points: int = 0
    portfolio: Optional[Dict[str, Any]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============== ONBOARDING MODELS ==============

class UserPreferences(BaseModel):
    experience_level: str
    preferred_markets: List[str]
    trading_goals: List[str]
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

# ============== CHAT MODELS ==============

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str

# ============== TRADING MODELS ==============

class PaperTrade(BaseModel):
    id: str
    user_id: str
    symbol: str
    type: str
    amount: float
    price: float
    timestamp: str
    status: str = "executed"

class PaperTradeCreate(BaseModel):
    symbol: str
    type: str
    amount: float
    price: float

class TradingSignal(BaseModel):
    id: str
    user_id: str
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
    created_at: str
    status: str = "active"
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

# ============== ALERT MODELS ==============

class AlertCreate(BaseModel):
    symbol: str
    target_price: float
    condition: str
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

class SmartAlertCreate(BaseModel):
    symbol: str
    condition_type: str
    value: float
    sound_enabled: bool = True
    repeat: bool = False
    name: Optional[str] = None

# ============== STRATEGY MODELS ==============

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

# ============== JOURNAL MODELS ==============

class TradeJournalEntry(BaseModel):
    id: str
    user_id: str
    symbol: str
    symbol_name: str
    trade_type: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    entry_date: str
    exit_date: Optional[str] = None
    timeframe: str
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    status: str = "open"
    pnl_amount: Optional[float] = None
    pnl_percent: Optional[float] = None
    emotion_before: Optional[str] = None
    emotion_after: Optional[str] = None
    strategy_used: Optional[str] = None
    reason_entry: str
    reason_exit: Optional[str] = None
    lessons_learned: Optional[str] = None
    screenshot_url: Optional[str] = None
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
