"""
Market Data Service - Centralized data fetching from multiple sources
Uses CryptoCompare as primary, with CoinGecko and Binance as fallbacks
"""
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from core.config import (
    COINGECKO_API_URL, 
    CRYPTOCOMPARE_API_URL, 
    BINANCE_API_URL,
    ALPHA_VANTAGE_API_KEY,
    logger
)

# Crypto symbol mapping
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

# Stock/Index symbols for Smart Invest
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


class MarketDataService:
    """Centralized service for fetching market data from multiple sources"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {
            "crypto_list": {"data": None, "timestamp": None, "ttl": 300},
            "crypto_prices": {"data": None, "timestamp": None, "ttl": 60},
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        cache = self._cache.get(cache_key)
        if not cache or not cache["data"] or not cache["timestamp"]:
            return False
        age = (datetime.now(timezone.utc) - cache["timestamp"]).total_seconds()
        return age < cache["ttl"]
    
    def _update_cache(self, cache_key: str, data: Any):
        """Update cache with new data"""
        self._cache[cache_key]["data"] = data
        self._cache[cache_key]["timestamp"] = datetime.now(timezone.utc)
    
    async def get_crypto_list(self) -> Optional[List[Dict]]:
        """Get list of top cryptocurrencies with current prices"""
        
        # Check cache first
        if self._is_cache_valid("crypto_list"):
            logger.info("Returning cached crypto list")
            return self._cache["crypto_list"]["data"]
        
        # Strategy 1: CryptoCompare (most reliable)
        data = await self._fetch_from_cryptocompare()
        if data:
            self._update_cache("crypto_list", data)
            return data
        
        # Strategy 2: CoinGecko (fallback)
        data = await self._fetch_from_coingecko()
        if data:
            self._update_cache("crypto_list", data)
            return data
        
        # Strategy 3: Binance (may be geo-blocked)
        data = await self._fetch_from_binance()
        if data:
            self._update_cache("crypto_list", data)
            return data
        
        # Return stale cache if available
        if self._cache["crypto_list"]["data"]:
            logger.warning("Returning stale cached crypto list")
            return self._cache["crypto_list"]["data"]
        
        return None
    
    async def _fetch_from_cryptocompare(self) -> Optional[List[Dict]]:
        """Fetch crypto data from CryptoCompare API"""
        try:
            symbols = "BTC,ETH,BNB,SOL,XRP,ADA,DOGE,AVAX,DOT,LINK,MATIC,LTC,SHIB,UNI,NEAR,TRX,XLM,ATOM,ETC,FIL"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/pricemultifull",
                    params={"fsyms": symbols, "tsyms": "USD"},
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                if "RAW" not in data:
                    return None
                
                # Map symbols to coin IDs
                symbol_to_id = {v["binance_symbol"]: k for k, v in CRYPTO_MAPPING.items()}
                
                crypto_list = []
                rank = 1
                
                for symbol, info in data["RAW"].items():
                    if "USD" not in info:
                        continue
                    
                    usd_data = info["USD"]
                    coin_id = symbol_to_id.get(symbol, symbol.lower())
                    
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
                
                crypto_list.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
                for i, crypto in enumerate(crypto_list):
                    crypto["market_cap_rank"] = i + 1
                
                logger.info(f"✅ Fetched {len(crypto_list)} cryptos from CryptoCompare")
                return crypto_list
                
        except Exception as e:
            logger.error(f"CryptoCompare API error: {e}")
            return None
    
    async def _fetch_from_coingecko(self) -> Optional[List[Dict]]:
        """Fetch crypto data from CoinGecko API"""
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
                    for item in data:
                        item["source"] = "coingecko"
                    logger.info(f"✅ Fetched {len(data)} cryptos from CoinGecko")
                    return data
                elif response.status_code == 429:
                    logger.warning("CoinGecko rate limited")
                return None
                
        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
            return None
    
    async def _fetch_from_binance(self) -> Optional[List[Dict]]:
        """Fetch crypto data from Binance API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BINANCE_API_URL}/ticker/24hr",
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    return None
                
                binance_data = response.json()
                binance_lookup = {item["symbol"]: item for item in binance_data}
                
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
                            "market_cap": float(ticker["quoteVolume"]) * 100,
                            "market_cap_rank": info["rank"],
                            "price_change_percentage_24h": float(ticker["priceChangePercent"]),
                            "high_24h": float(ticker["highPrice"]),
                            "low_24h": float(ticker["lowPrice"]),
                            "total_volume": float(ticker["volume"]),
                            "sparkline_in_7d": {"price": []},
                            "source": "binance"
                        })
                
                crypto_list.sort(key=lambda x: x["market_cap_rank"])
                logger.info(f"✅ Fetched {len(crypto_list)} cryptos from Binance")
                return crypto_list
                
        except Exception as e:
            logger.error(f"Binance API error: {e}")
            return None
    
    async def get_historical_prices(self, coin_id: str, days: int = 14) -> Optional[List[float]]:
        """Get historical price data for technical analysis"""
        
        # Get symbol from mapping
        crypto_symbol = None
        if coin_id in CRYPTO_MAPPING:
            crypto_symbol = CRYPTO_MAPPING[coin_id]["binance_symbol"]
        else:
            crypto_symbol = coin_id.upper()[:4]
        
        # Strategy 1: CryptoCompare
        prices = await self._fetch_historical_cryptocompare(crypto_symbol, days)
        if prices and len(prices) > 10:
            return prices
        
        # Strategy 2: CoinGecko
        prices = await self._fetch_historical_coingecko(coin_id, days)
        if prices and len(prices) > 10:
            return prices
        
        return None
    
    async def _fetch_historical_cryptocompare(self, symbol: str, days: int) -> Optional[List[float]]:
        """Fetch historical data from CryptoCompare"""
        try:
            api_type = "histoday" if days > 7 else "histohour"
            limit = days if days > 7 else days * 24
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/{api_type}",
                    params={"fsym": symbol, "tsym": "USD", "limit": limit},
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("Response") == "Success" and "Data" in data:
                        hist_data = data["Data"]
                        if isinstance(hist_data, list) and len(hist_data) > 10:
                            prices = [float(d["close"]) for d in hist_data if d.get("close")]
                            logger.info(f"✅ Got {len(prices)} historical prices from CryptoCompare for {symbol}")
                            return prices
            return None
        except Exception as e:
            logger.warning(f"CryptoCompare historical error for {symbol}: {e}")
            return None
    
    async def _fetch_historical_coingecko(self, coin_id: str, days: int) -> Optional[List[float]]:
        """Fetch historical data from CoinGecko"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": days},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prices = [p[1] for p in data.get("prices", [])]
                    logger.info(f"✅ Got {len(prices)} historical prices from CoinGecko for {coin_id}")
                    return prices
            return None
        except Exception as e:
            logger.warning(f"CoinGecko historical error for {coin_id}: {e}")
            return None
    
    async def get_crypto_prices(self, symbols: List[str]) -> Optional[Dict[str, Dict]]:
        """Get current prices for multiple symbols"""
        try:
            # Convert coin IDs to CryptoCompare symbols
            cc_symbols = []
            for s in symbols:
                if s in CRYPTO_MAPPING:
                    cc_symbols.append(CRYPTO_MAPPING[s]["binance_symbol"])
                else:
                    cc_symbols.append(s.upper())
            
            symbols_str = ",".join(cc_symbols)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{CRYPTOCOMPARE_API_URL}/pricemultifull",
                    params={"fsyms": symbols_str, "tsyms": "USD"},
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "RAW" in data:
                        return data["RAW"]
            return None
        except Exception as e:
            logger.error(f"Error fetching crypto prices: {e}")
            return None
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get stock/index data from Alpha Vantage"""
        if not ALPHA_VANTAGE_API_KEY:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "TIME_SERIES_DAILY",
                        "symbol": symbol,
                        "apikey": ALPHA_VANTAGE_API_KEY
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "Time Series (Daily)" in data:
                        return data
            return None
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return None


# Singleton instance
market_data_service = MarketDataService()
