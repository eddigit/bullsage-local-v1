"""
GMX V2 Configuration Module for BullSage
========================================

Ce module gère la configuration pour l'intégration GMX V2.
Le SDK gmx-python-sdk est compatible avec Python 3.10 et web3==6.10.0.

Installation requise:
    pip install gmx-python-sdk web3==6.10.0

Note: Python 3.10.x est recommandé pour une compatibilité optimale.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GMXConfig:
    """Configuration pour GMX V2 Trading"""
    
    # Network
    arbitrum_mainnet: bool = True
    avalanche_mainnet: bool = False
    
    # RPC
    arbitrum_rpc: str = "https://arb1.arbitrum.io/rpc"
    avalanche_rpc: str = "https://api.avax.network/ext/bc/C/rpc"
    
    # Chain IDs
    arbitrum_chain_id: int = 42161
    avalanche_chain_id: int = 43114
    
    # Trading
    use_paper_trading: bool = True
    default_leverage: int = 10
    max_slippage: float = 0.03
    debug_mode: bool = True
    
    # Wallet (from environment variables)
    private_key: Optional[str] = None
    wallet_address: Optional[str] = None
    
    # Risk Management
    max_position_size_usd: float = 10000
    max_open_positions: int = 5
    stop_loss_percent: float = 0.05
    take_profit_percent: float = 0.10


def load_gmx_config(config_path: Optional[str] = None) -> GMXConfig:
    """
    Charge la configuration GMX depuis le fichier YAML.
    
    Args:
        config_path: Chemin vers le fichier de configuration.
                     Par défaut: config/gmx.yaml
    
    Returns:
        GMXConfig: Instance de configuration
    """
    if config_path is None:
        config_path = Path(__file__).parent / "gmx.yaml"
    else:
        config_path = Path(config_path)
    
    config = GMXConfig()
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
        
        # Network
        if 'network' in yaml_config:
            config.arbitrum_mainnet = yaml_config['network'].get('arbitrum_mainnet', True)
            config.avalanche_mainnet = yaml_config['network'].get('avalanche_mainnet', False)
        
        # RPCs
        if 'rpcs' in yaml_config:
            config.arbitrum_rpc = yaml_config['rpcs'].get('arbitrum', config.arbitrum_rpc)
            config.avalanche_rpc = yaml_config['rpcs'].get('avalanche', config.avalanche_rpc)
        
        # Trading
        if 'trading' in yaml_config:
            config.use_paper_trading = yaml_config['trading'].get('use_paper_trading', True)
            config.default_leverage = yaml_config['trading'].get('default_leverage', 10)
            config.max_slippage = yaml_config['trading'].get('max_slippage', 0.03)
            config.debug_mode = yaml_config['trading'].get('debug_mode', True)
        
        # Risk Management
        if 'risk_management' in yaml_config:
            config.max_position_size_usd = yaml_config['risk_management'].get('max_position_size_usd', 10000)
            config.max_open_positions = yaml_config['risk_management'].get('max_open_positions', 5)
            config.stop_loss_percent = yaml_config['risk_management'].get('stop_loss_percent', 0.05)
            config.take_profit_percent = yaml_config['risk_management'].get('take_profit_percent', 0.10)
    
    # Load wallet from environment variables
    config.private_key = os.getenv('GMX_PRIVATE_KEY')
    config.wallet_address = os.getenv('GMX_WALLET_ADDRESS')
    
    return config


def get_gmx_sdk_config(chain: str = "arbitrum") -> Optional[Any]:
    """
    Initialise et retourne un ConfigManager du SDK GMX.
    
    Args:
        chain: "arbitrum" ou "avalanche"
    
    Returns:
        ConfigManager ou None si le SDK n'est pas disponible
    
    Note:
        Requiert gmx-python-sdk et Python 3.10.x
    """
    try:
        from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
        
        config = ConfigManager(chain=chain)
        
        # Load custom config
        gmx_config = load_gmx_config()
        
        # Set RPC
        if chain == "arbitrum":
            config.set_config(rpc=gmx_config.arbitrum_rpc)
        elif chain == "avalanche":
            config.set_config(rpc=gmx_config.avalanche_rpc)
        
        # Set wallet if available
        if gmx_config.private_key and gmx_config.wallet_address:
            config.set_config(
                private_key=gmx_config.private_key,
                user_wallet_address=gmx_config.wallet_address
            )
        
        return config
    
    except ImportError as e:
        print(f"Warning: GMX SDK not available - {e}")
        print("Install with: pip install gmx-python-sdk web3==6.10.0")
        print("Note: Python 3.10.x is recommended for compatibility")
        return None
    except Exception as e:
        print(f"Error initializing GMX SDK: {e}")
        return None


# Default markets on Arbitrum
ARBITRUM_MARKETS = {
    "ETH": {
        "symbol": "ETH",
        "index_token": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "market_key": "0x70d95587d40A2caf56bd97485aB3Eec10Bee6336"
    },
    "BTC": {
        "symbol": "BTC", 
        "index_token": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
        "market_key": "0x47c031236e19d024b42f8AE6780E44A573170703"
    },
    "ARB": {
        "symbol": "ARB",
        "index_token": "0x912CE59144191C1204E64559FE8253a0e49E6548",
        "market_key": "0xC25cEf6061Cf5dE5eb761b50E4743c1F5D7E5407"
    },
    "LINK": {
        "symbol": "LINK",
        "index_token": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
        "market_key": "0x7f1fa204bb700853D36994DA19F830b6Ad18455C"
    },
    "SOL": {
        "symbol": "SOL",
        "index_token": "0x2bcC6D6CdBbDC0a4071e48bb3B969b06B3330c07",
        "market_key": "0x09400D9DB990D5ed3f35D7be61DfAEB900Af03C9"
    }
}

# Collateral tokens on Arbitrum
ARBITRUM_COLLATERAL = {
    "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    "ETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "BTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
    "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
}


if __name__ == "__main__":
    # Test configuration loading
    config = load_gmx_config()
    print(f"GMX Config loaded:")
    print(f"  - Arbitrum Mainnet: {config.arbitrum_mainnet}")
    print(f"  - Paper Trading: {config.use_paper_trading}")
    print(f"  - Default Leverage: {config.default_leverage}x")
    print(f"  - Max Slippage: {config.max_slippage * 100}%")
    print(f"  - Debug Mode: {config.debug_mode}")
