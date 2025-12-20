from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from ..core.config import db
from ..core.auth import get_current_user
from ..models.schemas import OnboardingData

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

@router.post("/complete")
async def complete_onboarding(data: OnboardingData, current_user: dict = Depends(get_current_user)):
    """Complete the onboarding process and save user preferences"""
    
    level_map = {
        "beginner": "beginner",
        "intermediate": "intermediate",
        "confirmed": "advanced",
        "expert": "advanced"
    }
    trading_level = level_map.get(data.experience_level, "beginner")
    
    preferences = {
        "experience_level": data.experience_level,
        "preferred_markets": data.preferred_markets,
        "trading_goals": data.trading_goals,
        "favorite_assets": data.favorite_assets,
        "onboarding_date": datetime.now(timezone.utc).isoformat()
    }
    
    watchlist = []
    if "crypto" in data.preferred_markets and data.favorite_assets.get("crypto"):
        watchlist = data.favorite_assets["crypto"][:5]
    
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
    
    updated_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "password": 0})
    
    return {
        "success": True,
        "message": "Onboarding completed successfully",
        "user": updated_user
    }

@router.get("/status")
async def get_onboarding_status(current_user: dict = Depends(get_current_user)):
    """Check if user has completed onboarding"""
    return {
        "onboarding_completed": current_user.get("onboarding_completed", False),
        "preferences": current_user.get("preferences", None)
    }

@router.get("/options")
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
