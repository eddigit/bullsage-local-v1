#!/usr/bin/env python3
"""
🐂 BULL SAGE - Test Complet Bitcoin
====================================

Tests approfondis sur Bitcoin:
- Prix en temps réel via plusieurs APIs
- Analyse technique
- News du marché
- Prédictions du Council IA (tous les agents)
- Cohérence des signaux
- Trading Deribit

Usage:
    python test_bitcoin.py
    python test_bitcoin.py --full    # Avec appel au Council IA (lent)
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

import httpx

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api"


@dataclass
class BitcoinAnalysis:
    """Résultat de l'analyse Bitcoin"""
    timestamp: str
    prices: Dict[str, float]
    market_data: Dict[str, Any]
    news: List[Dict]
    technical_analysis: Dict[str, Any]
    ai_predictions: Dict[str, Any]
    deribit_data: Dict[str, Any]
    consistency_score: float
    summary: str


class BitcoinTestAgent:
    """Agent de test complet pour Bitcoin"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.results = {}
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()
    
    def _print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    
    def _print_result(self, label: str, value: Any, status: str = "✅"):
        print(f"  {status} {label}: {value}")
    
    # ==================== PRIX BITCOIN ====================
    
    async def get_bitcoin_prices(self) -> Dict[str, float]:
        """Récupérer les prix Bitcoin depuis plusieurs sources"""
        self._print_section("💰 PRIX BITCOIN - MULTI-SOURCES")
        
        prices = {}
        
        # 1. CoinGecko
        try:
            resp = await self.client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd,eur", "include_24hr_change": "true"}
            )
            if resp.status_code == 200:
                data = resp.json()
                prices["coingecko_usd"] = data["bitcoin"]["usd"]
                prices["coingecko_eur"] = data["bitcoin"]["eur"]
                prices["coingecko_24h_change"] = data["bitcoin"].get("usd_24h_change", 0)
                self._print_result("CoinGecko", f"${prices['coingecko_usd']:,.2f} (24h: {prices['coingecko_24h_change']:.2f}%)")
        except Exception as e:
            self._print_result("CoinGecko", str(e), "❌")
        
        # 2. Deribit (BTC-PERPETUAL)
        try:
            resp = await self.client.get(f"{API_URL}/deribit/ticker/BTC-PERPETUAL")
            if resp.status_code == 200:
                data = resp.json()
                ticker = data.get("ticker", data)
                prices["deribit_perpetual"] = ticker.get("last_price") or ticker.get("mark_price", 0)
                prices["deribit_index"] = ticker.get("index_price", 0)
                prices["deribit_funding"] = ticker.get("current_funding", 0)
                self._print_result("Deribit Perpetual", f"${prices['deribit_perpetual']:,.2f}")
                self._print_result("Deribit Index", f"${prices['deribit_index']:,.2f}")
        except Exception as e:
            self._print_result("Deribit", str(e), "❌")
        
        # 3. Calcul de la divergence
        if prices.get("coingecko_usd") and prices.get("deribit_perpetual"):
            divergence = abs(prices["coingecko_usd"] - prices["deribit_perpetual"]) / prices["coingecko_usd"] * 100
            prices["price_divergence"] = divergence
            status = "✅" if divergence < 0.5 else "⚠️" if divergence < 1 else "❌"
            self._print_result("Divergence prix", f"{divergence:.3f}%", status)
        
        self.results["prices"] = prices
        return prices
    
    # ==================== DONNÉES MARCHÉ ====================
    
    async def get_market_data(self) -> Dict[str, Any]:
        """Récupérer les données de marché étendues"""
        self._print_section("📊 DONNÉES MARCHÉ BITCOIN")
        
        market_data = {}
        
        # CoinGecko - Données étendues
        try:
            resp = await self.client.get(
                "https://api.coingecko.com/api/v3/coins/bitcoin",
                params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}
            )
            if resp.status_code == 200:
                data = resp.json()
                md = data.get("market_data", {})
                
                market_data["market_cap"] = md.get("market_cap", {}).get("usd", 0)
                market_data["total_volume"] = md.get("total_volume", {}).get("usd", 0)
                market_data["circulating_supply"] = md.get("circulating_supply", 0)
                market_data["ath"] = md.get("ath", {}).get("usd", 0)
                market_data["ath_date"] = md.get("ath_date", {}).get("usd", "")
                market_data["atl"] = md.get("atl", {}).get("usd", 0)
                market_data["price_change_7d"] = md.get("price_change_percentage_7d", 0)
                market_data["price_change_30d"] = md.get("price_change_percentage_30d", 0)
                
                self._print_result("Market Cap", f"${market_data['market_cap']/1e9:,.2f}B")
                self._print_result("Volume 24h", f"${market_data['total_volume']/1e9:,.2f}B")
                self._print_result("ATH", f"${market_data['ath']:,.2f} ({market_data['ath_date'][:10]})")
                self._print_result("Change 7j", f"{market_data['price_change_7d']:.2f}%")
                self._print_result("Change 30j", f"{market_data['price_change_30d']:.2f}%")
        except Exception as e:
            self._print_result("CoinGecko Market Data", str(e), "❌")
        
        # Fear & Greed Index (via alternative.me)
        try:
            resp = await self.client.get("https://api.alternative.me/fng/", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                fng = data.get("data", [{}])[0]
                market_data["fear_greed_index"] = int(fng.get("value", 50))
                market_data["fear_greed_label"] = fng.get("value_classification", "Neutral")
                
                # Emoji selon le niveau
                idx = market_data["fear_greed_index"]
                emoji = "😱" if idx < 25 else "😰" if idx < 45 else "😐" if idx < 55 else "😊" if idx < 75 else "🤑"
                self._print_result("Fear & Greed", f"{idx} - {market_data['fear_greed_label']} {emoji}")
        except Exception as e:
            self._print_result("Fear & Greed Index", str(e), "⚠️")
        
        self.results["market_data"] = market_data
        return market_data
    
    # ==================== NEWS BITCOIN ====================
    
    async def get_bitcoin_news(self) -> List[Dict]:
        """Récupérer les news Bitcoin récentes"""
        self._print_section("📰 NEWS BITCOIN")
        
        news = []
        
        # Essayer plusieurs sources de news
        try:
            # CryptoCompare News API (gratuit)
            resp = await self.client.get(
                "https://min-api.cryptocompare.com/data/v2/news/",
                params={"categories": "BTC", "lang": "EN"},
                timeout=15.0
            )
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("Data", [])[:5]
                
                for article in articles:
                    news.append({
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "url": article.get("url", ""),
                        "published": datetime.fromtimestamp(article.get("published_on", 0)).strftime("%Y-%m-%d %H:%M")
                    })
                    
                print(f"  📰 {len(news)} articles récents:")
                for i, n in enumerate(news[:3], 1):
                    print(f"     {i}. [{n['source']}] {n['title'][:60]}...")
        except Exception as e:
            self._print_result("CryptoCompare News", str(e), "⚠️")
        
        # Finnhub News
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if finnhub_key:
            try:
                resp = await self.client.get(
                    f"https://finnhub.io/api/v1/news",
                    params={"category": "crypto", "token": finnhub_key},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    articles = resp.json()[:3]
                    finnhub_count = 0
                    for article in articles:
                        if "bitcoin" in article.get("headline", "").lower() or "btc" in article.get("headline", "").lower():
                            news.append({
                                "title": article.get("headline", ""),
                                "source": article.get("source", "Finnhub"),
                                "url": article.get("url", ""),
                                "published": datetime.fromtimestamp(article.get("datetime", 0)).strftime("%Y-%m-%d %H:%M")
                            })
                            finnhub_count += 1
                    if finnhub_count > 0:
                        self._print_result("Finnhub News", f"+{finnhub_count} articles")
            except Exception as e:
                pass
        
        self.results["news"] = news
        return news
    
    # ==================== ANALYSE TECHNIQUE ====================
    
    async def get_technical_analysis(self) -> Dict[str, Any]:
        """Analyse technique Bitcoin"""
        self._print_section("📈 ANALYSE TECHNIQUE")
        
        ta = {}
        
        # Récupérer les données OHLCV
        try:
            resp = await self.client.get(
                "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc",
                params={"vs_currency": "usd", "days": "30"}
            )
            if resp.status_code == 200:
                ohlc = resp.json()
                
                if len(ohlc) > 0:
                    # Dernières valeurs
                    latest = ohlc[-1]
                    ta["last_open"] = latest[1]
                    ta["last_high"] = latest[2]
                    ta["last_low"] = latest[3]
                    ta["last_close"] = latest[4]
                    
                    # Calcul simple de tendance
                    closes = [x[4] for x in ohlc[-14:]]  # 14 dernières périodes
                    if len(closes) >= 14:
                        sma_7 = sum(closes[-7:]) / 7
                        sma_14 = sum(closes) / 14
                        ta["sma_7"] = sma_7
                        ta["sma_14"] = sma_14
                        ta["trend"] = "BULLISH" if sma_7 > sma_14 else "BEARISH"
                        
                        # RSI simplifié (14 périodes)
                        gains = []
                        losses = []
                        for i in range(1, len(closes)):
                            diff = closes[i] - closes[i-1]
                            if diff > 0:
                                gains.append(diff)
                                losses.append(0)
                            else:
                                gains.append(0)
                                losses.append(abs(diff))
                        
                        avg_gain = sum(gains) / len(gains) if gains else 0
                        avg_loss = sum(losses) / len(losses) if losses else 1
                        
                        if avg_loss > 0:
                            rs = avg_gain / avg_loss
                            ta["rsi_14"] = 100 - (100 / (1 + rs))
                        else:
                            ta["rsi_14"] = 100
                        
                        # Volatilité (écart-type)
                        mean = sum(closes) / len(closes)
                        variance = sum((x - mean) ** 2 for x in closes) / len(closes)
                        ta["volatility"] = (variance ** 0.5) / mean * 100
                        
                        # Affichage
                        trend_emoji = "🟢" if ta["trend"] == "BULLISH" else "🔴"
                        self._print_result("Tendance", f"{ta['trend']} {trend_emoji}")
                        self._print_result("SMA 7", f"${ta['sma_7']:,.2f}")
                        self._print_result("SMA 14", f"${ta['sma_14']:,.2f}")
                        
                        rsi = ta["rsi_14"]
                        rsi_status = "🔴 Surachat" if rsi > 70 else "🟢 Survente" if rsi < 30 else "⚪ Neutre"
                        self._print_result("RSI 14", f"{rsi:.1f} {rsi_status}")
                        self._print_result("Volatilité", f"{ta['volatility']:.2f}%")
        except Exception as e:
            self._print_result("OHLCV Data", str(e), "❌")
        
        self.results["technical"] = ta
        return ta
    
    # ==================== COUNCIL IA ====================
    
    async def get_ai_predictions(self, full_analysis: bool = False) -> Dict[str, Any]:
        """Obtenir les prédictions du Council IA"""
        self._print_section("🧠 COUNCIL IA - PRÉDICTIONS")
        
        predictions = {}
        
        # Vérifier les agents disponibles
        agents_config = {
            "Claude (Anthropic)": bool(os.getenv("ANTHROPIC_API_KEY")),
            "Groq": bool(os.getenv("GROQ_API_KEY")),
            "Grok (xAI)": bool(os.getenv("XAI_API_KEY")),
            "OpenRouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "DeepSeek": bool(os.getenv("DEEPSEEK_API_KEY")),
            "Perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
        }
        
        available = [name for name, configured in agents_config.items() if configured]
        predictions["available_agents"] = available
        
        print(f"  🤖 Agents IA disponibles: {len(available)}/6")
        for agent in available:
            print(f"     ✅ {agent}")
        
        if full_analysis:
            print("\n  🔄 Lancement de l'analyse du Council (peut prendre 30-60s)...")
            
            try:
                resp = await self.client.post(
                    f"{API_URL}/council/quick-analysis",
                    json={"symbol": "BTC", "timeframe": "1h"},
                    timeout=120.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    predictions["council_response"] = data
                    predictions["recommendation"] = data.get("recommendation", "N/A")
                    predictions["confidence"] = data.get("confidence", 0)
                    predictions["analysis"] = data.get("analysis", "")
                    
                    rec = predictions["recommendation"]
                    conf = predictions["confidence"]
                    emoji = "🚀" if "BUY" in rec.upper() else "📉" if "SELL" in rec.upper() else "⏸️"
                    
                    self._print_result("Recommandation", f"{rec} {emoji}")
                    self._print_result("Confiance", f"{conf}%")
                    
                    if predictions.get("analysis"):
                        print(f"\n  📝 Analyse:\n     {predictions['analysis'][:200]}...")
                        
                elif resp.status_code == 503:
                    self._print_result("Council", "Temporairement indisponible", "⚠️")
                else:
                    self._print_result("Council", f"Erreur {resp.status_code}", "❌")
            except asyncio.TimeoutError:
                self._print_result("Council", "Timeout (>120s)", "⚠️")
            except Exception as e:
                self._print_result("Council", str(e), "❌")
        else:
            print("  ℹ️ Utilisez --full pour lancer l'analyse complète du Council")
        
        self.results["predictions"] = predictions
        return predictions
    
    # ==================== DERIBIT DATA ====================
    
    async def get_deribit_data(self) -> Dict[str, Any]:
        """Données de trading Deribit"""
        self._print_section("📈 DERIBIT TRADING DATA")
        
        deribit = {}
        
        # Compte
        try:
            resp = await self.client.get(f"{API_URL}/deribit/account", params={"currency": "BTC"})
            if resp.status_code == 200:
                data = resp.json()
                account = data.get("account", {})
                deribit["equity"] = account.get("equity", 0)
                deribit["balance"] = account.get("balance", 0)
                deribit["available_funds"] = account.get("available_funds", 0)
                
                self._print_result("Équité", f"{deribit['equity']} BTC")
                self._print_result("Balance", f"{deribit['balance']} BTC")
                self._print_result("Fonds disponibles", f"{deribit['available_funds']} BTC")
        except Exception as e:
            self._print_result("Compte Deribit", str(e), "❌")
        
        # Positions
        try:
            resp = await self.client.get(f"{API_URL}/deribit/positions", params={"currency": "BTC"})
            if resp.status_code == 200:
                data = resp.json()
                positions = data.get("positions", [])
                deribit["positions"] = positions
                deribit["positions_count"] = len(positions)
                
                if positions:
                    total_pnl = sum(p.get("floating_profit_loss", 0) for p in positions)
                    deribit["total_pnl"] = total_pnl
                    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
                    self._print_result("Positions ouvertes", len(positions))
                    self._print_result("PnL total", f"{total_pnl:.6f} BTC {pnl_emoji}")
                else:
                    self._print_result("Positions ouvertes", "0")
        except Exception as e:
            self._print_result("Positions Deribit", str(e), "❌")
        
        # Ticker détaillé
        try:
            resp = await self.client.get(f"{API_URL}/deribit/ticker/BTC-PERPETUAL")
            if resp.status_code == 200:
                data = resp.json()
                ticker = data.get("ticker", data)
                deribit["open_interest"] = ticker.get("open_interest", 0)
                deribit["funding_rate"] = ticker.get("current_funding", 0)
                deribit["best_bid"] = ticker.get("best_bid_price", 0)
                deribit["best_ask"] = ticker.get("best_ask_price", 0)
                
                spread = deribit["best_ask"] - deribit["best_bid"]
                spread_pct = spread / deribit["best_bid"] * 100 if deribit["best_bid"] else 0
                
                self._print_result("Open Interest", f"${deribit['open_interest']:,.0f}")
                self._print_result("Funding Rate", f"{deribit['funding_rate']*100:.4f}%")
                self._print_result("Spread", f"${spread:.2f} ({spread_pct:.4f}%)")
        except Exception as e:
            pass
        
        self.results["deribit"] = deribit
        return deribit
    
    # ==================== SCORE DE COHÉRENCE ====================
    
    def calculate_consistency_score(self) -> float:
        """Calculer un score de cohérence global"""
        self._print_section("🎯 SCORE DE COHÉRENCE")
        
        score = 100.0
        factors = []
        
        # 1. Divergence des prix (max 20 points)
        prices = self.results.get("prices", {})
        if prices.get("price_divergence"):
            div = prices["price_divergence"]
            price_score = max(0, 20 - div * 10)
            score -= (20 - price_score)
            factors.append(f"Prix divergence: -{20-price_score:.1f}pts")
        
        # 2. RSI extrême (max 15 points)
        ta = self.results.get("technical", {})
        if ta.get("rsi_14"):
            rsi = ta["rsi_14"]
            if rsi > 80 or rsi < 20:
                score -= 15
                factors.append("RSI extrême: -15pts")
            elif rsi > 70 or rsi < 30:
                score -= 8
                factors.append("RSI élevé/bas: -8pts")
        
        # 3. Fear & Greed extrême (max 10 points)
        md = self.results.get("market_data", {})
        if md.get("fear_greed_index"):
            fng = md["fear_greed_index"]
            if fng < 20 or fng > 80:
                score -= 10
                factors.append("Fear/Greed extrême: -10pts")
            elif fng < 30 or fng > 70:
                score -= 5
                factors.append("Fear/Greed élevé: -5pts")
        
        # 4. Volatilité élevée (max 10 points)
        if ta.get("volatility"):
            vol = ta["volatility"]
            if vol > 5:
                score -= 10
                factors.append("Haute volatilité: -10pts")
            elif vol > 3:
                score -= 5
                factors.append("Volatilité modérée: -5pts")
        
        score = max(0, min(100, score))
        
        # Affichage
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🟠" if score >= 40 else "🔴"
        self._print_result("Score de cohérence", f"{score:.1f}/100 {emoji}")
        
        if factors:
            print("  📋 Facteurs de risque:")
            for f in factors:
                print(f"     • {f}")
        
        return score
    
    # ==================== RÉSUMÉ ====================
    
    def generate_summary(self) -> str:
        """Générer un résumé de l'analyse"""
        self._print_section("📋 RÉSUMÉ DE L'ANALYSE")
        
        prices = self.results.get("prices", {})
        ta = self.results.get("technical", {})
        md = self.results.get("market_data", {})
        deribit = self.results.get("deribit", {})
        
        # Construction du résumé
        lines = []
        
        # Prix
        if prices.get("coingecko_usd"):
            change = prices.get("coingecko_24h_change", 0)
            direction = "↗️" if change > 0 else "↘️" if change < 0 else "→"
            lines.append(f"💰 Bitcoin: ${prices['coingecko_usd']:,.2f} ({change:+.2f}% 24h) {direction}")
        
        # Tendance
        if ta.get("trend"):
            emoji = "🟢" if ta["trend"] == "BULLISH" else "🔴"
            lines.append(f"📈 Tendance: {ta['trend']} {emoji}")
        
        # RSI
        if ta.get("rsi_14"):
            rsi = ta["rsi_14"]
            zone = "Surachat" if rsi > 70 else "Survente" if rsi < 30 else "Neutre"
            lines.append(f"📊 RSI: {rsi:.1f} ({zone})")
        
        # Fear & Greed
        if md.get("fear_greed_index"):
            lines.append(f"😰 Sentiment: {md['fear_greed_index']} ({md.get('fear_greed_label', 'N/A')})")
        
        # Deribit
        if deribit.get("equity"):
            lines.append(f"💼 Deribit: {deribit['equity']} BTC | {deribit.get('positions_count', 0)} positions")
        
        summary = "\n  ".join(lines)
        print(f"  {summary}")
        
        return summary
    
    # ==================== EXÉCUTION ====================
    
    async def run_full_analysis(self, include_council: bool = False):
        """Exécuter l'analyse complète"""
        print("\n" + "🐂"*30)
        print("   BULL SAGE - ANALYSE COMPLÈTE BITCOIN")
        print("   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🐂"*30)
        
        # Collecter toutes les données
        await self.get_bitcoin_prices()
        await self.get_market_data()
        await self.get_bitcoin_news()
        await self.get_technical_analysis()
        await self.get_ai_predictions(full_analysis=include_council)
        await self.get_deribit_data()
        
        # Calculer le score
        score = self.calculate_consistency_score()
        
        # Générer le résumé
        summary = self.generate_summary()
        
        # Conclusion
        print("\n" + "="*60)
        if score >= 80:
            print("  ✅ MARCHÉ STABLE - Conditions favorables pour le trading")
        elif score >= 60:
            print("  ⚠️ PRUDENCE RECOMMANDÉE - Quelques signaux contradictoires")
        elif score >= 40:
            print("  🟠 RISQUE MODÉRÉ - Surveiller attentivement le marché")
        else:
            print("  🔴 RISQUE ÉLEVÉ - Éviter les positions importantes")
        print("="*60 + "\n")
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"test_reports/bitcoin_analysis_{timestamp}.json"
        os.makedirs("test_reports", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "consistency_score": score,
                "summary": summary,
                **self.results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Rapport sauvegardé: {filepath}")
        
        return self.results


async def main():
    parser = argparse.ArgumentParser(description="🐂 Bull Sage - Analyse Bitcoin")
    parser.add_argument("--full", action="store_true", help="Inclure l'analyse du Council IA (lent)")
    args = parser.parse_args()
    
    async with BitcoinTestAgent() as agent:
        await agent.run_full_analysis(include_council=args.full)


if __name__ == "__main__":
    asyncio.run(main())
