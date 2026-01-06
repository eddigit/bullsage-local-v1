import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import logging

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'bullsage_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# API Keys & URLs
XAI_API_KEY = os.environ.get('XAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
XAI_BASE_URL = "https://api.x.ai/v1"
EMERGENT_LLM_KEY = XAI_API_KEY  # Backward compatibility
COINGECKO_API_URL = os.environ.get('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')
CRYPTOCOMPARE_API_URL = "https://min-api.cryptocompare.com/data"
BINANCE_API_URL = "https://api.binance.com/api/v3"
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
FRED_API_KEY = os.environ.get('FRED_API_KEY')
MARKETAUX_API_KEY = os.environ.get('MARKETAUX_API_KEY')

# dYdX Configuration
DYDX_TESTNET_MNEMONIC = os.environ.get('DYDX_TESTNET_MNEMONIC', '')
DYDX_TESTNET_ADDRESS = os.environ.get('DYDX_TESTNET_ADDRESS', '')
DYDX_MAINNET_MNEMONIC = os.environ.get('DYDX_MAINNET_MNEMONIC', '')
DYDX_MAINNET_ADDRESS = os.environ.get('DYDX_MAINNET_ADDRESS', '')

# dYdX Executor Service (Node.js)
DYDX_EXECUTOR_URL = os.environ.get('DYDX_EXECUTOR_URL', 'http://localhost:3001')
DYDX_API_SECRET = os.environ.get('DYDX_API_SECRET', '')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
