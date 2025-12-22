"""DeFi Scanner Routes - Scan for hot tokens on DEXes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import httpx
import asyncio

from ..core.config import db, logger, EMERGENT_LLM_KEY
from ..core.auth import get_current_user

router = APIRouter(prefix="/defi-scanner", tags=["DeFi Scanner"])

# ============== MODELS ==============

class TokenInfo(BaseModel):
    """Token information from DEX"""
    address: str
    symbol: str
    name: str
    chain: str
    price_usd: float
    price_change_24h: float
    price_change_1h: Optional[float] = None
    volume_24h: float
    liquidity: float
    market_cap: Optional[float] = None
    fdv: Optional[float] = None
    tx_count_24h: Optional[int] = None
    buyers_24h: Optional[int] = None
    sellers_24h: Optional[int] = None
    source: str
    dex: Optional[str] = None
    pair_address: Optional[str] = None
    created_at: Optional[str] = None
    score: Optional[float] = None

class ScanResult(BaseModel):
    """Scan result with tokens"""
    tokens: List[TokenInfo]
    scan_time: str
    source: str
    chain: Optional[str] = None

# ============== DEX SCANNER SERVICES ==============

async def scan_dexscreener(chain: str = None, limit: int = 20) -> List[Dict]:
    """Scan DexScreener for trending tokens"""
    try:
        async with httpx.AsyncClient() as client:
            # Get trending/boosted tokens
            url = "https://api.dexscreener.com/token-boosts/latest/v1"
            response = await client.get(url, timeout=15.0)
            
            tokens = []
            if response.status_code == 200:
                data = response.json()
                
                for item in data[:limit]:
                    token_address = item.get("tokenAddress", "")
                    chain_id = item.get("chainId", "unknown")
                    
                    # Filter by chain if specified
                    if chain and chain.lower() != chain_id.lower():
                        continue
                    
                    # Get detailed pair info
                    try:
                        pair_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                        pair_resp = await client.get(pair_url, timeout=10.0)
                        if pair_resp.status_code == 200:
                            pair_data = pair_resp.json()
                            pairs = pair_data.get("pairs", [])
                            if pairs:
                                pair = pairs[0]  # Get the main pair
                                tokens.append({
                                    "address": token_address,
                                    "symbol": pair.get("baseToken", {}).get("symbol", "?"),
                                    "name": pair.get("baseToken", {}).get("name", "Unknown"),
                                    "chain": chain_id,
                                    "price_usd": float(pair.get("priceUsd", 0) or 0),
                                    "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                                    "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0) or 0),
                                    "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                                    "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                                    "fdv": float(pair.get("fdv", 0) or 0),
                                    "tx_count_24h": pair.get("txns", {}).get("h24", {}).get("buys", 0) + pair.get("txns", {}).get("h24", {}).get("sells", 0),
                                    "buyers_24h": pair.get("txns", {}).get("h24", {}).get("buys", 0),
                                    "sellers_24h": pair.get("txns", {}).get("h24", {}).get("sells", 0),
                                    "source": "dexscreener",
                                    "dex": pair.get("dexId", "unknown"),
                                    "pair_address": pair.get("pairAddress", ""),
                                    "created_at": pair.get("pairCreatedAt", "")
                                })
                    except Exception as e:
                        logger.warning(f"Error fetching pair for {token_address}: {e}")
                        continue
                    
                    await asyncio.sleep(0.1)  # Rate limiting
            
            logger.info(f"DexScreener: Found {len(tokens)} tokens")
            return tokens
            
    except Exception as e:
        logger.error(f"DexScreener scan error: {e}")
        return []

async def scan_birdeye(chain: str = "solana", limit: int = 20) -> List[Dict]:
    """Scan Birdeye for trending Solana tokens"""
    try:
        async with httpx.AsyncClient() as client:
            # Birdeye public API for trending tokens
            url = "https://public-api.birdeye.so/defi/tokenlist"
            headers = {"X-API-KEY": "public"}  # Public endpoint
            
            response = await client.get(
                url,
                params={
                    "sort_by": "v24hChangePercent",
                    "sort_type": "desc",
                    "offset": 0,
                    "limit": limit
                },
                headers=headers,
                timeout=15.0
            )
            
            tokens = []
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("tokens", [])
                
                for item in items:
                    tokens.append({
                        "address": item.get("address", ""),
                        "symbol": item.get("symbol", "?"),
                        "name": item.get("name", "Unknown"),
                        "chain": "solana",
                        "price_usd": float(item.get("price", 0) or 0),
                        "price_change_24h": float(item.get("v24hChangePercent", 0) or 0),
                        "volume_24h": float(item.get("v24hUSD", 0) or 0),
                        "liquidity": float(item.get("liquidity", 0) or 0),
                        "market_cap": float(item.get("mc", 0) or 0),
                        "source": "birdeye",
                        "dex": "raydium/orca"
                    })
            
            logger.info(f"Birdeye: Found {len(tokens)} tokens")
            return tokens
            
    except Exception as e:
        logger.error(f"Birdeye scan error: {e}")
        return []

async def scan_geckoterminal(chain: str = "solana", limit: int = 20) -> List[Dict]:
    """Scan GeckoTerminal for trending tokens"""
    try:
        # Map chain names to GeckoTerminal network IDs
        chain_map = {
            "solana": "solana",
            "ethereum": "eth",
            "bsc": "bsc",
            "polygon": "polygon_pos",
            "arbitrum": "arbitrum",
            "base": "base"
        }
        
        network = chain_map.get(chain.lower(), "solana")
        
        async with httpx.AsyncClient() as client:
            # Get trending pools
            url = f"https://api.geckoterminal.com/api/v2/networks/{network}/trending_pools"
            response = await client.get(url, timeout=15.0)
            
            tokens = []
            if response.status_code == 200:
                data = response.json()
                pools = data.get("data", [])
                
                for pool in pools[:limit]:
                    attrs = pool.get("attributes", {})
                    tokens.append({
                        "address": attrs.get("address", ""),
                        "symbol": attrs.get("name", "?").split("/")[0] if "/" in attrs.get("name", "") else attrs.get("name", "?"),
                        "name": attrs.get("name", "Unknown"),
                        "chain": chain,
                        "price_usd": float(attrs.get("base_token_price_usd", 0) or 0),
                        "price_change_24h": float(attrs.get("price_change_percentage", {}).get("h24", 0) or 0),
                        "price_change_1h": float(attrs.get("price_change_percentage", {}).get("h1", 0) or 0),
                        "volume_24h": float(attrs.get("volume_usd", {}).get("h24", 0) or 0),
                        "liquidity": float(attrs.get("reserve_in_usd", 0) or 0),
                        "fdv": float(attrs.get("fdv_usd", 0) or 0),
                        "tx_count_24h": int(attrs.get("transactions", {}).get("h24", {}).get("buys", 0) or 0) + int(attrs.get("transactions", {}).get("h24", {}).get("sells", 0) or 0),
                        "source": "geckoterminal",
                        "dex": attrs.get("dex_id", "unknown"),
                        "pair_address": attrs.get("address", "")
                    })
            
            logger.info(f"GeckoTerminal: Found {len(tokens)} tokens on {network}")
            return tokens
            
    except Exception as e:
        logger.error(f"GeckoTerminal scan error: {e}")
        return []

def calculate_token_score(token: Dict) -> float:
    """Calculate a score for a token based on multiple factors"""
    score = 0.0
    
    # Volume score (0-25 points)
    volume = token.get("volume_24h", 0)
    if volume > 1000000:  # >$1M
        score += 25
    elif volume > 100000:  # >$100K
        score += 20
    elif volume > 10000:  # >$10K
        score += 10
    
    # Liquidity score (0-25 points)
    liquidity = token.get("liquidity", 0)
    if liquidity > 500000:  # >$500K
        score += 25
    elif liquidity > 100000:  # >$100K
        score += 20
    elif liquidity > 10000:  # >$10K
        score += 10
    
    # Price momentum (0-30 points)
    change_24h = token.get("price_change_24h", 0)
    change_1h = token.get("price_change_1h", 0)
    
    if 10 < change_24h < 100:  # Good momentum but not extreme
        score += 20
    elif 5 < change_24h <= 10:
        score += 15
    elif change_24h > 100:  # Too volatile, risky
        score += 5
    
    if change_1h and 2 < change_1h < 20:
        score += 10
    
    # Buy/Sell ratio (0-20 points)
    buyers = token.get("buyers_24h", 0)
    sellers = token.get("sellers_24h", 0)
    if buyers and sellers:
        ratio = buyers / max(sellers, 1)
        if ratio > 1.5:  # More buyers than sellers
            score += 20
        elif ratio > 1.2:
            score += 15
        elif ratio > 1:
            score += 10
    
    return min(score, 100)  # Max 100

# ============== ROUTES ==============

@router.get("/scan")
async def scan_defi_tokens(
    chain: Optional[str] = Query(None, description="Chain to scan: solana, ethereum, bsc, polygon"),
    source: Optional[str] = Query(None, description="Source: dexscreener, birdeye, geckoterminal, all"),
    limit: int = Query(20, ge=5, le=50),
    min_liquidity: float = Query(10000, description="Minimum liquidity in USD"),
    min_volume: float = Query(5000, description="Minimum 24h volume in USD"),
    current_user: dict = Depends(get_current_user)
):
    """Scan DEXes for trending tokens with smart filters"""
    
    all_tokens = []
    sources_used = []
    
    # Determine which sources to use
    if source == "dexscreener" or source is None or source == "all":
        tokens = await scan_dexscreener(chain, limit)
        all_tokens.extend(tokens)
        if tokens:
            sources_used.append("dexscreener")
    
    if source == "birdeye" or source == "all":
        if chain is None or chain == "solana":
            tokens = await scan_birdeye("solana", limit)
            all_tokens.extend(tokens)
            if tokens:
                sources_used.append("birdeye")
    
    if source == "geckoterminal" or source is None or source == "all":
        scan_chain = chain or "solana"
        tokens = await scan_geckoterminal(scan_chain, limit)
        all_tokens.extend(tokens)
        if tokens:
            sources_used.append("geckoterminal")
    
    # Filter tokens
    filtered_tokens = []
    seen_addresses = set()
    
    for token in all_tokens:
        # Skip duplicates
        addr = token.get("address", "").lower()
        if addr in seen_addresses:
            continue
        seen_addresses.add(addr)
        
        # Apply filters
        if token.get("liquidity", 0) < min_liquidity:
            continue
        if token.get("volume_24h", 0) < min_volume:
            continue
        
        # Calculate score
        token["score"] = calculate_token_score(token)
        filtered_tokens.append(token)
    
    # Sort by score
    filtered_tokens.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Log scan to database
    await db.defi_scans.insert_one({
        "user_id": current_user["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chain": chain,
        "sources": sources_used,
        "tokens_found": len(filtered_tokens),
        "filters": {
            "min_liquidity": min_liquidity,
            "min_volume": min_volume
        }
    })
    
    return {
        "tokens": filtered_tokens[:limit],
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "sources": sources_used,
        "chain": chain or "all",
        "total_found": len(filtered_tokens),
        "filters_applied": {
            "min_liquidity": min_liquidity,
            "min_volume": min_volume
        }
    }

@router.get("/trending/{chain}")
async def get_trending_tokens(
    chain: str,
    limit: int = Query(10, ge=5, le=30),
    current_user: dict = Depends(get_current_user)
):
    """Get trending tokens for a specific chain"""
    
    tokens = await scan_geckoterminal(chain, limit)
    
    # Calculate scores
    for token in tokens:
        token["score"] = calculate_token_score(token)
    
    # Sort by score
    tokens.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {
        "chain": chain,
        "tokens": tokens,
        "scan_time": datetime.now(timezone.utc).isoformat()
    }

@router.get("/token/{chain}/{address}")
async def get_token_details(
    chain: str,
    address: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific token"""
    try:
        chain_map = {
            "solana": "solana",
            "ethereum": "eth",
            "bsc": "bsc",
            "polygon": "polygon_pos"
        }
        network = chain_map.get(chain.lower(), chain)
        
        async with httpx.AsyncClient() as client:
            # Get token info from GeckoTerminal
            url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
            response = await client.get(url, timeout=15.0)
            
            if response.status_code == 200:
                data = response.json()
                token_data = data.get("data", {}).get("attributes", {})
                
                # Get pools for this token
                pools_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}/pools"
                pools_resp = await client.get(pools_url, timeout=10.0)
                pools = []
                if pools_resp.status_code == 200:
                    pools_data = pools_resp.json()
                    pools = pools_data.get("data", [])
                
                return {
                    "address": address,
                    "chain": chain,
                    "name": token_data.get("name", "Unknown"),
                    "symbol": token_data.get("symbol", "?"),
                    "price_usd": float(token_data.get("price_usd", 0) or 0),
                    "fdv": float(token_data.get("fdv_usd", 0) or 0),
                    "market_cap": float(token_data.get("market_cap_usd", 0) or 0),
                    "total_supply": token_data.get("total_supply", "0"),
                    "pools_count": len(pools),
                    "top_pools": [
                        {
                            "address": p.get("attributes", {}).get("address", ""),
                            "dex": p.get("attributes", {}).get("dex_id", ""),
                            "volume_24h": float(p.get("attributes", {}).get("volume_usd", {}).get("h24", 0) or 0),
                            "liquidity": float(p.get("attributes", {}).get("reserve_in_usd", 0) or 0)
                        }
                        for p in pools[:5]
                    ]
                }
            
            raise HTTPException(status_code=404, detail="Token non trouvé")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token detail error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des données")

@router.get("/watchlist")
async def get_defi_watchlist(current_user: dict = Depends(get_current_user)):
    """Get user's DeFi token watchlist"""
    watchlist = await db.defi_watchlist.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    return watchlist

@router.post("/watchlist")
async def add_to_defi_watchlist(
    token_address: str,
    chain: str,
    symbol: str,
    name: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a token to DeFi watchlist"""
    
    # Check if already in watchlist
    existing = await db.defi_watchlist.find_one({
        "user_id": current_user["id"],
        "address": token_address.lower(),
        "chain": chain
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Token déjà dans la watchlist")
    
    doc = {
        "user_id": current_user["id"],
        "address": token_address.lower(),
        "chain": chain,
        "symbol": symbol,
        "name": name,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.defi_watchlist.insert_one(doc)
    return {"message": "Token ajouté à la watchlist"}

@router.delete("/watchlist/{token_address}")
async def remove_from_defi_watchlist(
    token_address: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a token from DeFi watchlist"""
    result = await db.defi_watchlist.delete_one({
        "user_id": current_user["id"],
        "address": token_address.lower()
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Token non trouvé dans la watchlist")
    
    return {"message": "Token retiré de la watchlist"}

@router.get("/history")
async def get_scan_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get user's scan history"""
    history = await db.defi_scans.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return history
