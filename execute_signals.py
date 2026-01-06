#!/usr/bin/env python3
"""
🐂 BULL SAGE - Exécuteur dYdX via Node.js subprocess

Exécute des signaux sur dYdX en appelant le script Node.js existant
"""
import subprocess
import json
import os
import sys
from pathlib import Path


# Chemin vers le script execute.js
EXECUTOR_PATH = Path(__file__).parent / "dydx-executor" / "execute.js"


def execute_signal(market: str, direction: str, size: float, 
                   entry: float = None, stop_loss: float = None, 
                   take_profit: float = None) -> dict:
    """
    Exécute un signal sur dYdX via le script Node.js
    
    Args:
        market: ex. "BTC-USD", "ETH-USD", "SOL-USD"
        direction: "LONG" ou "SHORT"
        size: Taille de la position (0.001 pour BTC, 0.01 pour ETH, 0.1 pour SOL)
        entry: Prix d'entrée (optionnel, sinon market order)
        stop_loss: Prix du stop loss (optionnel)
        take_profit: Prix du take profit (optionnel)
    
    Returns:
        dict avec les résultats de l'exécution
    """
    # Construire les arguments
    args = ["node", str(EXECUTOR_PATH), market, direction, str(size)]
    
    if entry:
        args.extend(["--entry", str(entry)])
    if stop_loss:
        args.extend(["--sl", str(stop_loss)])
    if take_profit:
        args.extend(["--tp", str(take_profit)])
    
    print(f"\n🎯 Exécution: {direction} {market} x{size}")
    print(f"   Commande: {' '.join(args)}")
    
    try:
        # Exécuter le script Node.js
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes max
            cwd=str(Path(__file__).parent)
        )
        
        output = result.stdout + result.stderr
        
        # Chercher le JSON de résultat dans la sortie
        if result.returncode == 0:
            print(f"   ✅ Succès!")
            # Chercher les ordres exécutés
            for line in output.split('\n'):
                if '✅' in line or '📊' in line or 'OrderId' in line:
                    print(f"      {line.strip()}")
            
            return {
                "success": True,
                "market": market,
                "direction": direction,
                "size": size,
                "output": output
            }
        else:
            print(f"   ❌ Erreur (code {result.returncode})")
            print(f"      {output[:500]}")
            return {
                "success": False,
                "error": output,
                "return_code": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout après 120s")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {"success": False, "error": str(e)}


def execute_btc_long():
    """Exécute un signal BTC LONG"""
    return execute_signal("BTC-USD", "LONG", 0.001, 
                          stop_loss=103000, take_profit=108000)


def execute_eth_long():
    """Exécute un signal ETH LONG"""
    return execute_signal("ETH-USD", "LONG", 0.01,
                          stop_loss=2400, take_profit=2700)


def execute_sol_long():
    """Exécute un signal SOL LONG"""
    return execute_signal("SOL-USD", "LONG", 0.1,
                          stop_loss=145, take_profit=165)


def main():
    print("=" * 60)
    print("🐂 BULL SAGE - Exécution de signaux dYdX")
    print("=" * 60)
    
    # Vérifier que le script execute.js existe
    if not EXECUTOR_PATH.exists():
        print(f"❌ Script non trouvé: {EXECUTOR_PATH}")
        sys.exit(1)
    
    # Exécuter les 3 signaux
    results = []
    
    print("\n" + "─" * 40)
    print("📊 Signal 1: BTC-USD LONG")
    print("─" * 40)
    results.append(execute_btc_long())
    
    print("\n" + "─" * 40)
    print("📊 Signal 2: ETH-USD LONG")
    print("─" * 40)
    results.append(execute_eth_long())
    
    print("\n" + "─" * 40)
    print("📊 Signal 3: SOL-USD LONG")
    print("─" * 40)
    results.append(execute_sol_long())
    
    # Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r.get("success"))
    print(f"   Ordres réussis: {success_count}/{len(results)}")
    
    print("\n💡 Vérifiez vos positions sur:")
    print("   https://v4.testnet.dydx.exchange/portfolio/positions")
    

if __name__ == "__main__":
    main()
