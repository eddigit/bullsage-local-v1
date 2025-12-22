"""Wallet Routes - DeFi Wallet Integration (Phantom, MetaMask)"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import httpx
import uuid

from ..core.config import db, logger
from ..core.auth import get_current_user

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# ============== MODELS ==============

class WalletConnect(BaseModel):
    """Model for connecting a wallet"""
    wallet_type: str  # 'phantom' or 'metamask'
    address: str
    chain: str = "solana"  # 'solana', 'ethereum', 'polygon', 'bsc'
    signature: Optional[str] = None  # For verification

class WalletResponse(BaseModel):
    """Response model for wallet info"""
    id: str
    user_id: str
    wallet_type: str
    address: str
    chain: str
    connected_at: str
    is_primary: bool = False
    balance: Optional[float] = None
    tokens: List[Dict[str, Any]] = []

class WalletBalance(BaseModel):
    """Balance information"""
    native_balance: float
    native_symbol: str
    usd_value: float
    tokens: List[Dict[str, Any]]

# ============== CHAIN CONFIGURATIONS ==============

CHAIN_CONFIG = {
    "solana": {
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "native_symbol": "SOL",
        "explorer": "https://solscan.io",
        "decimals": 9
    },
    "ethereum": {
        "rpc_url": "https://eth.llamarpc.com",
        "native_symbol": "ETH",
        "explorer": "https://etherscan.io",
        "decimals": 18
    },
    "polygon": {
        "rpc_url": "https://polygon-rpc.com",
        "native_symbol": "MATIC",
        "explorer": "https://polygonscan.com",
        "decimals": 18
    },
    "bsc": {
        "rpc_url": "https://bsc-dataseed.binance.org",
        "native_symbol": "BNB",
        "explorer": "https://bscscan.com",
        "decimals": 18
    }
}

# ============== HELPER FUNCTIONS ==============

async def get_solana_balance(address: str) -> Dict[str, Any]:
    """Get Solana wallet balance using public RPC"""
    try:
        async with httpx.AsyncClient() as client:
            # Get SOL balance
            response = await client.post(
                CHAIN_CONFIG["solana"]["rpc_url"],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [address]
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    lamports = data["result"]["value"]
                    sol_balance = lamports / 1e9  # Convert lamports to SOL
                    
                    # Get SOL price
                    price_resp = await client.get(
                        "https://min-api.cryptocompare.com/data/price?fsym=SOL&tsyms=USD",
                        timeout=5.0
                    )
                    sol_price = 0
                    if price_resp.status_code == 200:
                        sol_price = price_resp.json().get("USD", 0)
                    
                    return {
                        "native_balance": sol_balance,
                        "native_symbol": "SOL",
                        "usd_value": sol_balance * sol_price,
                        "tokens": []
                    }
            return None
    except Exception as e:
        logger.error(f"Solana balance error: {e}")
        return None

async def get_evm_balance(address: str, chain: str) -> Dict[str, Any]:
    """Get EVM wallet balance (Ethereum, Polygon, BSC)"""
    try:
        config = CHAIN_CONFIG.get(chain)
        if not config:
            return None
        
        async with httpx.AsyncClient() as client:
            # Get native balance
            response = await client.post(
                config["rpc_url"],
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBalance",
                    "params": [address, "latest"]
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    wei = int(data["result"], 16)
                    balance = wei / (10 ** config["decimals"])
                    
                    # Get price
                    symbol = config["native_symbol"]
                    price_resp = await client.get(
                        f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms=USD",
                        timeout=5.0
                    )
                    price = 0
                    if price_resp.status_code == 200:
                        price = price_resp.json().get("USD", 0)
                    
                    return {
                        "native_balance": balance,
                        "native_symbol": symbol,
                        "usd_value": balance * price,
                        "tokens": []
                    }
            return None
    except Exception as e:
        logger.error(f"EVM balance error for {chain}: {e}")
        return None

# ============== ROUTES ==============

@router.post("/connect", response_model=WalletResponse)
async def connect_wallet(
    wallet_data: WalletConnect,
    current_user: dict = Depends(get_current_user)
):
    """Connect a DeFi wallet to user account"""
    
    # Validate wallet type
    if wallet_data.wallet_type not in ["phantom", "metamask"]:
        raise HTTPException(status_code=400, detail="Type de wallet non supporté. Utilisez 'phantom' ou 'metamask'")
    
    # Validate chain
    if wallet_data.chain not in CHAIN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Chain non supportée. Utilisez: {', '.join(CHAIN_CONFIG.keys())}")
    
    # Check if wallet already connected
    existing = await db.wallets.find_one({
        "user_id": current_user["id"],
        "address": wallet_data.address.lower()
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Ce wallet est déjà connecté à votre compte")
    
    # Check if this is the first wallet (make it primary)
    wallet_count = await db.wallets.count_documents({"user_id": current_user["id"]})
    is_primary = wallet_count == 0
    
    # Create wallet record
    wallet_id = str(uuid.uuid4())
    wallet_doc = {
        "id": wallet_id,
        "user_id": current_user["id"],
        "wallet_type": wallet_data.wallet_type,
        "address": wallet_data.address.lower(),
        "chain": wallet_data.chain,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "is_primary": is_primary
    }
    
    await db.wallets.insert_one(wallet_doc)
    logger.info(f"Wallet connected: {wallet_data.wallet_type} - {wallet_data.address[:10]}... for user {current_user['id']}")
    
    return WalletResponse(**wallet_doc)

@router.get("/list")
async def list_wallets(current_user: dict = Depends(get_current_user)):
    """List all connected wallets for user"""
    wallets = await db.wallets.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    return wallets

@router.get("/{wallet_id}/balance")
async def get_wallet_balance(
    wallet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get balance for a connected wallet"""
    wallet = await db.wallets.find_one({
        "id": wallet_id,
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet non trouvé")
    
    # Get balance based on chain
    balance = None
    if wallet["chain"] == "solana":
        balance = await get_solana_balance(wallet["address"])
    else:
        balance = await get_evm_balance(wallet["address"], wallet["chain"])
    
    if not balance:
        raise HTTPException(status_code=503, detail="Impossible de récupérer le solde. Réessayez plus tard.")
    
    return {
        "wallet_id": wallet_id,
        "address": wallet["address"],
        "chain": wallet["chain"],
        **balance
    }

@router.delete("/{wallet_id}")
async def disconnect_wallet(
    wallet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Disconnect a wallet from user account"""
    result = await db.wallets.delete_one({
        "id": wallet_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wallet non trouvé")
    
    logger.info(f"Wallet disconnected: {wallet_id} for user {current_user['id']}")
    return {"message": "Wallet déconnecté avec succès"}

@router.put("/{wallet_id}/primary")
async def set_primary_wallet(
    wallet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Set a wallet as the primary wallet"""
    # Verify wallet exists
    wallet = await db.wallets.find_one({
        "id": wallet_id,
        "user_id": current_user["id"]
    })
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet non trouvé")
    
    # Remove primary from all other wallets
    await db.wallets.update_many(
        {"user_id": current_user["id"]},
        {"$set": {"is_primary": False}}
    )
    
    # Set this wallet as primary
    await db.wallets.update_one(
        {"id": wallet_id},
        {"$set": {"is_primary": True}}
    )
    
    return {"message": "Wallet défini comme principal"}

@router.get("/supported-chains")
async def get_supported_chains():
    """Get list of supported blockchain networks"""
    chains = []
    for chain_id, config in CHAIN_CONFIG.items():
        chains.append({
            "id": chain_id,
            "name": chain_id.capitalize(),
            "native_symbol": config["native_symbol"],
            "explorer": config["explorer"],
            "wallet_type": "phantom" if chain_id == "solana" else "metamask"
        })
    return chains
