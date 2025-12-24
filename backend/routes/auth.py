from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import jwt
import bcrypt

from ..core.config import db, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from ..core.auth import get_current_user
from ..models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiry
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register", response_model=TokenResponse)
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

@router.post("/login", response_model=TokenResponse)
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
        is_admin=user.get("is_admin", False),
        onboarding_completed=user.get("onboarding_completed", False),
        preferences=user.get("preferences"),
        avatar=user.get("avatar"),
        points=user.get("points", 0),
        portfolio=user.get("portfolio", {})
    )
    
    return TokenResponse(access_token=token, user=user_response)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        trading_level=current_user.get("trading_level", "beginner"),
        created_at=current_user["created_at"],
        paper_balance=current_user.get("paper_balance", 10000.0),
        watchlist=current_user.get("watchlist", []),
        is_admin=current_user.get("is_admin", False),
        onboarding_completed=current_user.get("onboarding_completed", False),
        preferences=current_user.get("preferences"),
        avatar=current_user.get("avatar"),
        points=current_user.get("points", 0),
        portfolio=current_user.get("portfolio", {})
    )
