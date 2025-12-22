"""Newsletter Service - Daily market analysis newsletter"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import logging

logger = logging.getLogger(__name__)

class NewsletterService:
    def __init__(self, db, llm_client=None):
        self.db = db
        self.llm_client = llm_client
        self.smtp_config = None
    
    async def load_smtp_config(self):
        """Load SMTP configuration from database"""
        config = await self.db.settings.find_one({"type": "smtp_config"}, {"_id": 0})
        if config:
            self.smtp_config = config
        return config
    
    async def save_smtp_config(self, config: Dict[str, Any]):
        """Save SMTP configuration to database"""
        config["type"] = "smtp_config"
        config["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.db.settings.update_one(
            {"type": "smtp_config"},
            {"$set": config},
            upsert=True
        )
        self.smtp_config = config
        return config
    
    async def get_market_data(self) -> Dict[str, Any]:
        """Fetch current market data for newsletter"""
        market_data = {
            "top_cryptos": [],
            "top_gainers": [],
            "top_losers": [],
            "fear_greed_index": None,
            "btc_dominance": None
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Get top cryptos from CryptoCompare
                response = await client.get(
                    "https://min-api.cryptocompare.com/data/top/mktcapfull",
                    params={"limit": 10, "tsym": "USD"},
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("Data", [])[:10]:
                        coin_info = item.get("CoinInfo", {})
                        raw = item.get("RAW", {}).get("USD", {})
                        market_data["top_cryptos"].append({
                            "symbol": coin_info.get("Name", ""),
                            "name": coin_info.get("FullName", ""),
                            "price": raw.get("PRICE", 0),
                            "change_24h": raw.get("CHANGEPCT24HOUR", 0),
                            "market_cap": raw.get("MKTCAP", 0),
                            "volume_24h": raw.get("VOLUME24HOURTO", 0)
                        })
                
                # Sort for gainers/losers
                sorted_by_change = sorted(
                    market_data["top_cryptos"], 
                    key=lambda x: x.get("change_24h", 0), 
                    reverse=True
                )
                market_data["top_gainers"] = sorted_by_change[:3]
                market_data["top_losers"] = sorted_by_change[-3:]
                
                # Fear & Greed Index
                fg_response = await client.get(
                    "https://api.alternative.me/fng/",
                    timeout=10.0
                )
                if fg_response.status_code == 200:
                    fg_data = fg_response.json()
                    if fg_data.get("data"):
                        market_data["fear_greed_index"] = {
                            "value": int(fg_data["data"][0].get("value", 50)),
                            "label": fg_data["data"][0].get("value_classification", "Neutral")
                        }
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
        
        return market_data
    
    async def get_trending_tokens(self) -> List[Dict]:
        """Get trending DeFi tokens"""
        trending = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.geckoterminal.com/api/v2/networks/solana/trending_pools",
                    timeout=15.0
                )
                if response.status_code == 200:
                    data = response.json()
                    for pool in data.get("data", [])[:5]:
                        attrs = pool.get("attributes", {})
                        trending.append({
                            "name": attrs.get("name", "Unknown"),
                            "price_change_24h": float(attrs.get("price_change_percentage", {}).get("h24", 0) or 0),
                            "volume_24h": float(attrs.get("volume_usd", {}).get("h24", 0) or 0)
                        })
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
        
        return trending
    
    async def get_top_traders_activity(self) -> List[Dict]:
        """Get recent trades from top performing users (paper trading)"""
        try:
            # Get users with best performance
            pipeline = [
                {"$match": {"result": "win"}},
                {"$group": {
                    "_id": "$user_id",
                    "wins": {"$sum": 1},
                    "total_profit": {"$sum": "$profit_loss"}
                }},
                {"$sort": {"total_profit": -1}},
                {"$limit": 5}
            ]
            
            top_traders = await self.db.paper_trades.aggregate(pipeline).to_list(5)
            
            # Get their recent trades
            recent_trades = []
            for trader in top_traders:
                user = await self.db.users.find_one({"id": trader["_id"]}, {"name": 1, "email": 1})
                trades = await self.db.paper_trades.find(
                    {"user_id": trader["_id"]},
                    {"_id": 0}
                ).sort("created_at", -1).limit(2).to_list(2)
                
                for trade in trades:
                    recent_trades.append({
                        "trader": user.get("name", "Trader Anonyme") if user else "Trader",
                        "symbol": trade.get("symbol", ""),
                        "action": trade.get("action", ""),
                        "profit": trade.get("profit_loss", 0)
                    })
            
            return recent_trades[:5]
        except Exception as e:
            logger.error(f"Error fetching top traders: {e}")
            return []
    
    async def generate_ai_analysis(self, market_data: Dict) -> Dict[str, str]:
        """Generate AI-powered market analysis"""
        analysis = {
            "summary": "",
            "btc_outlook": "",
            "trade_tips": [],
            "risk_warning": ""
        }
        
        if not self.llm_client:
            # Fallback without AI
            fg = market_data.get("fear_greed_index", {})
            fg_value = fg.get("value", 50) if fg else 50
            fg_label = fg.get("label", "Neutral") if fg else "Neutral"
            
            if fg_value < 30:
                analysis["summary"] = "🔴 Marché en zone de peur extrême. Opportunités d'achat potentielles pour les investisseurs patients."
                analysis["btc_outlook"] = "Bitcoin pourrait rebondir depuis ces niveaux de peur. Surveillez les supports clés."
            elif fg_value > 70:
                analysis["summary"] = "🟢 Marché en zone de cupidité. Prudence recommandée, prises de profits possibles."
                analysis["btc_outlook"] = "Bitcoin en zone de surchauffe. Attention aux corrections potentielles."
            else:
                analysis["summary"] = "🟡 Marché neutre avec une volatilité modérée. Bonne période pour analyser les opportunités."
                analysis["btc_outlook"] = "Bitcoin consolide. Attendez une cassure claire avant de prendre position."
            
            analysis["trade_tips"] = [
                "Ne risquez jamais plus de 2% de votre capital par trade",
                "Utilisez toujours des stop-loss pour protéger vos positions",
                "Suivez la tendance générale du marché",
                f"Fear & Greed Index: {fg_value} ({fg_label})"
            ]
            analysis["risk_warning"] = "⚠️ Le trading comporte des risques. N'investissez que ce que vous pouvez vous permettre de perdre."
            
            return analysis
        
        try:
            # Build prompt for AI
            top_cryptos = market_data.get("top_cryptos", [])[:5]
            gainers = market_data.get("top_gainers", [])
            losers = market_data.get("top_losers", [])
            fg = market_data.get("fear_greed_index", {})
            
            prompt = f"""En tant qu'analyste crypto expert, génère une analyse de marché concise pour une newsletter quotidienne.

Données du marché:
- Fear & Greed Index: {fg.get('value', 'N/A')} ({fg.get('label', 'N/A')})
- Top Gainers 24h: {', '.join([f"{g['symbol']} (+{g['change_24h']:.1f}%)" for g in gainers])}
- Top Losers 24h: {', '.join([f"{l['symbol']} ({l['change_24h']:.1f}%)" for l in losers])}
- BTC Price: ${top_cryptos[0]['price']:,.2f} ({top_cryptos[0]['change_24h']:+.1f}%) si disponible

Génère en français:
1. SUMMARY: Un résumé du marché en 2 phrases (avec emoji)
2. BTC_OUTLOOK: Perspective Bitcoin en 1-2 phrases
3. TIPS: 3 conseils de trading concrets pour aujourd'hui
4. FORMAT: JSON avec les clés summary, btc_outlook, tips (array)"""

            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content
            # Try to parse JSON from response
            if "{" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                ai_data = json.loads(json_str)
                analysis["summary"] = ai_data.get("summary", analysis["summary"])
                analysis["btc_outlook"] = ai_data.get("btc_outlook", analysis["btc_outlook"])
                analysis["trade_tips"] = ai_data.get("tips", analysis["trade_tips"])
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
        
        analysis["risk_warning"] = "⚠️ Le trading comporte des risques. N'investissez que ce que vous pouvez vous permettre de perdre."
        return analysis
    
    def generate_html_newsletter(
        self, 
        market_data: Dict, 
        analysis: Dict, 
        trending: List,
        top_trades: List
    ) -> str:
        """Generate HTML newsletter content"""
        
        date_str = datetime.now().strftime("%d/%m/%Y")
        
        # Format top cryptos table
        crypto_rows = ""
        for crypto in market_data.get("top_cryptos", [])[:7]:
            change = crypto.get("change_24h", 0)
            change_color = "#22c55e" if change >= 0 else "#ef4444"
            change_icon = "▲" if change >= 0 else "▼"
            crypto_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #333;">{crypto.get('symbol', '')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #333;">${crypto.get('price', 0):,.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid #333; color: {change_color};">{change_icon} {abs(change):.2f}%</td>
            </tr>
            """
        
        # Format trending tokens
        trending_html = ""
        for token in trending[:5]:
            change = token.get("price_change_24h", 0)
            change_color = "#22c55e" if change >= 0 else "#ef4444"
            trending_html += f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                <strong>{token.get('name', 'Unknown')}</strong>
                <span style="color: {change_color}; float: right;">{change:+.1f}%</span>
            </div>
            """
        
        # Format top trades
        trades_html = ""
        for trade in top_trades[:5]:
            profit = trade.get("profit", 0)
            profit_color = "#22c55e" if profit >= 0 else "#ef4444"
            trades_html += f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                <strong>{trade.get('trader', 'Trader')}</strong> - {trade.get('symbol', '')} ({trade.get('action', '')})
                <span style="color: {profit_color}; float: right;">${profit:+.2f}</span>
            </div>
            """
        
        # Format tips
        tips_html = ""
        for tip in analysis.get("trade_tips", []):
            tips_html += f"<li style='margin: 8px 0;'>{tip}</li>"
        
        # Fear & Greed
        fg = market_data.get("fear_greed_index", {})
        fg_value = fg.get("value", 50) if fg else 50
        fg_label = fg.get("label", "Neutral") if fg else "Neutral"
        fg_color = "#ef4444" if fg_value < 30 else "#22c55e" if fg_value > 70 else "#eab308"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        
        <!-- Header -->
        <div style="text-align: center; padding: 30px 0; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 16px;">
            <h1 style="margin: 0; color: #000; font-size: 28px;">🐂 BULL SAGE</h1>
            <p style="margin: 5px 0 0; color: #333;">Newsletter Quotidienne - {date_str}</p>
        </div>
        
        <!-- Summary -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #FFD700;">
            <h2 style="color: #FFD700; margin-top: 0;">📊 Résumé du Marché</h2>
            <p style="color: #e5e5e5; line-height: 1.6;">{analysis.get('summary', 'Analyse en cours...')}</p>
        </div>
        
        <!-- Fear & Greed -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
            <h3 style="color: #9ca3af; margin-top: 0;">Fear & Greed Index</h3>
            <div style="font-size: 48px; font-weight: bold; color: {fg_color};">{fg_value}</div>
            <div style="color: {fg_color}; font-size: 18px;">{fg_label}</div>
        </div>
        
        <!-- Top Cryptos -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #FFD700; margin-top: 0;">💰 Top Cryptomonnaies</h2>
            <table style="width: 100%; border-collapse: collapse; color: #e5e5e5;">
                <thead>
                    <tr style="border-bottom: 2px solid #FFD700;">
                        <th style="padding: 12px; text-align: left;">Crypto</th>
                        <th style="padding: 12px; text-align: left;">Prix</th>
                        <th style="padding: 12px; text-align: left;">24h</th>
                    </tr>
                </thead>
                <tbody>
                    {crypto_rows}
                </tbody>
            </table>
        </div>
        
        <!-- BTC Outlook -->
        <div style="background: linear-gradient(135deg, #f7931a22 0%, #16162a 100%); border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #f7931a; margin-top: 0;">₿ Bitcoin Outlook</h2>
            <p style="color: #e5e5e5; line-height: 1.6;">{analysis.get('btc_outlook', 'Analyse Bitcoin en cours...')}</p>
        </div>
        
        <!-- Trending DeFi -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #FFD700; margin-top: 0;">🔥 Tendances DeFi</h2>
            {trending_html if trending_html else '<p style="color: #9ca3af;">Aucune donnée disponible</p>'}
        </div>
        
        <!-- Top Traders -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <h2 style="color: #FFD700; margin-top: 0;">🏆 Trades des Meilleurs</h2>
            {trades_html if trades_html else '<p style="color: #9ca3af;">Aucun trade récent</p>'}
        </div>
        
        <!-- Trading Tips -->
        <div style="background: #16162a; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #22c55e;">
            <h2 style="color: #22c55e; margin-top: 0;">💡 Conseils du Jour</h2>
            <ul style="color: #e5e5e5; padding-left: 20px; line-height: 1.8;">
                {tips_html}
            </ul>
        </div>
        
        <!-- Risk Warning -->
        <div style="background: #ef444422; border-radius: 12px; padding: 15px; margin: 20px 0; text-align: center;">
            <p style="color: #fca5a5; margin: 0; font-size: 14px;">
                {analysis.get('risk_warning', '⚠️ Le trading comporte des risques.')}
            </p>
        </div>
        
        <!-- Footer -->
        <div style="text-align: center; padding: 20px; color: #666;">
            <p style="margin: 5px 0;">BULL SAGE - Votre Assistant Trading IA</p>
            <p style="margin: 5px 0; font-size: 12px;">
                <a href="#" style="color: #FFD700;">Se désabonner</a>
            </p>
        </div>
        
    </div>
</body>
</html>
        """
        
        return html
    
    async def send_newsletter(self, to_email: str, html_content: str) -> bool:
        """Send newsletter email via SMTP"""
        if not self.smtp_config:
            await self.load_smtp_config()
        
        if not self.smtp_config:
            logger.error("SMTP not configured")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.smtp_config.get("from_email", self.smtp_config.get("username"))
            message["To"] = to_email
            message["Subject"] = f"🐂 BULL SAGE - Newsletter du {datetime.now().strftime('%d/%m/%Y')}"
            
            # Add HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_config.get("host", "smtp.gmail.com"),
                port=self.smtp_config.get("port", 587),
                username=self.smtp_config.get("username"),
                password=self.smtp_config.get("password"),
                start_tls=True
            )
            
            logger.info(f"Newsletter sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send newsletter to {to_email}: {e}")
            return False
    
    async def send_daily_newsletter(self):
        """Main function to generate and send daily newsletter to all subscribers"""
        logger.info("Starting daily newsletter generation...")
        
        # Load SMTP config
        await self.load_smtp_config()
        if not self.smtp_config or not self.smtp_config.get("enabled"):
            logger.warning("Newsletter disabled or SMTP not configured")
            return {"sent": 0, "failed": 0, "disabled": True}
        
        # Get all subscribed users
        subscribers = await self.db.users.find(
            {"newsletter_subscribed": {"$ne": False}},
            {"email": 1, "name": 1}
        ).to_list(10000)
        
        if not subscribers:
            logger.info("No subscribers found")
            return {"sent": 0, "failed": 0, "no_subscribers": True}
        
        # Generate newsletter content
        market_data = await self.get_market_data()
        trending = await self.get_trending_tokens()
        top_trades = await self.get_top_traders_activity()
        analysis = await self.generate_ai_analysis(market_data)
        
        html_content = self.generate_html_newsletter(
            market_data, analysis, trending, top_trades
        )
        
        # Send to all subscribers
        sent = 0
        failed = 0
        
        for subscriber in subscribers:
            email = subscriber.get("email")
            if email:
                success = await self.send_newsletter(email, html_content)
                if success:
                    sent += 1
                else:
                    failed += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        # Log the newsletter send
        await self.db.newsletter_logs.insert_one({
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "subscribers_count": len(subscribers),
            "sent": sent,
            "failed": failed
        })
        
        logger.info(f"Newsletter completed: {sent} sent, {failed} failed")
        return {"sent": sent, "failed": failed, "total": len(subscribers)}


# Singleton instance
newsletter_service = None

def get_newsletter_service(db, llm_client=None):
    global newsletter_service
    if newsletter_service is None:
        newsletter_service = NewsletterService(db, llm_client)
    return newsletter_service
