from fastapi import APIRouter

# Import all routers
from .auth import router as auth_router
from .market import router as market_router
from .trading import router as trading_router
from .signals import router as signals_router
from .journal import router as journal_router
from .alerts import router as alerts_router
from .assistant import router as assistant_router
from .paper_trading import router as paper_trading_router
from .academy import router as academy_router
from .admin import router as admin_router
from .onboarding import router as onboarding_router
from .watchlist import router as watchlist_router
from .strategies import router as strategies_router
from .settings import router as settings_router
from .health import router as health_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(market_router)
api_router.include_router(trading_router)
api_router.include_router(signals_router)
api_router.include_router(journal_router)
api_router.include_router(alerts_router)
api_router.include_router(assistant_router)
api_router.include_router(paper_trading_router)
api_router.include_router(academy_router)
api_router.include_router(admin_router)
api_router.include_router(onboarding_router)
api_router.include_router(watchlist_router)
api_router.include_router(strategies_router)
api_router.include_router(settings_router)
api_router.include_router(health_router)
