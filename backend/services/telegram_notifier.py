"""
Service de notifications Telegram pour BULL SAGE
Envoie des alertes de trading en temps réel
"""

import asyncio
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Gestionnaire de notifications Telegram"""
    
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.info("ℹ️ Telegram non configuré - notifications désactivées")
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Envoie un message Telegram"""
        if not self.enabled:
            logger.debug(f"[TELEGRAM DISABLED] {text[:100]}...")
            return False
        
        url = self.BASE_URL.format(token=self.bot_token, method="sendMessage")
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ Message Telegram envoyé")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Erreur Telegram: {error}")
                        return False
        except Exception as e:
            logger.error(f"❌ Exception Telegram: {e}")
            return False
    
    async def send_trade_alert(self, 
                                symbol: str, 
                                action: str, 
                                price: float,
                                reason: str,
                                targets: Dict = None) -> bool:
        """Envoie une alerte de trading formatée"""
        
        emoji = "🟢" if action.upper() in ["BUY", "STRONG_BUY"] else "🔴" if action.upper() in ["SELL", "STRONG_SELL"] else "🟡"
        
        message = f"""
{emoji} <b>ALERTE TRADING - {symbol}</b>

📊 <b>Action:</b> {action.upper()}
💰 <b>Prix:</b> ${price:,.2f}
📝 <b>Raison:</b> {reason}
"""
        
        if targets:
            message += f"""
🎯 <b>Objectifs:</b>
   • TP1: ${targets.get('tp1', 'N/A')}
   • TP2: ${targets.get('tp2', 'N/A')}
   • SL: ${targets.get('stop_loss', 'N/A')}
"""
        
        message += f"\n⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        return await self.send_message(message)
    
    async def send_price_alert(self, 
                                symbol: str, 
                                current_price: float,
                                target_price: float,
                                condition: str) -> bool:
        """Envoie une alerte de prix atteint"""
        
        direction = "au-dessus de" if condition == "above" else "en-dessous de"
        
        message = f"""
🔔 <b>ALERTE PRIX - {symbol}</b>

💰 Prix actuel: <b>${current_price:,.2f}</b>
🎯 Objectif: ${target_price:,.2f}
📈 Le prix est passé {direction} votre cible!

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        return await self.send_message(message)
    
    async def send_daily_summary(self, 
                                  portfolio_value: float,
                                  daily_pnl: float,
                                  daily_pnl_percent: float,
                                  top_movers: List[Dict] = None) -> bool:
        """Envoie un résumé quotidien"""
        
        pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
        pnl_sign = "+" if daily_pnl >= 0 else ""
        
        message = f"""
📊 <b>RÉSUMÉ QUOTIDIEN BULL SAGE</b>

💼 <b>Valeur Portfolio:</b> ${portfolio_value:,.2f}
{pnl_emoji} <b>P&L Jour:</b> {pnl_sign}${daily_pnl:,.2f} ({pnl_sign}{daily_pnl_percent:.2f}%)
"""
        
        if top_movers:
            message += "\n🏆 <b>Top Movers:</b>\n"
            for i, mover in enumerate(top_movers[:5], 1):
                change_sign = "+" if mover.get('change', 0) >= 0 else ""
                message += f"   {i}. {mover['symbol']}: {change_sign}{mover['change']:.2f}%\n"
        
        message += f"\n⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        return await self.send_message(message)
    
    async def send_confluence_alert(self,
                                     symbol: str,
                                     score: float,
                                     direction: str,
                                     aligned_tf: int,
                                     recommendation: str) -> bool:
        """Envoie une alerte de confluence de signaux"""
        
        if score < 50:
            return False
        
        emoji = "🎯" if score > 70 else "📊"
        
        message = f"""
{emoji} <b>CONFLUENCE DÉTECTÉE - {symbol}</b>

📈 <b>Direction:</b> {direction}
💪 <b>Score:</b> {score:.1f}/100
🕐 <b>Timeframes alignés:</b> {aligned_tf}/6

💡 <b>Recommandation:</b>
{recommendation}

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        return await self.send_message(message)
    
    def configure(self, bot_token: str, chat_id: str) -> bool:
        """Configure les credentials Telegram"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        
        if self.enabled:
            logger.info("✅ Telegram configuré avec succès")
        
        return self.enabled
    
    async def test_connection(self) -> Dict:
        """Teste la connexion Telegram"""
        if not self.enabled:
            return {"success": False, "error": "Telegram non configuré"}
        
        url = self.BASE_URL.format(token=self.bot_token, method="getMe")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        bot_info = data.get("result", {})
                        
                        test_sent = await self.send_message("🐂 <b>BULL SAGE</b> connecté!")
                        
                        return {
                            "success": True,
                            "bot_name": bot_info.get("username"),
                            "test_message_sent": test_sent
                        }
                    else:
                        return {"success": False, "error": "Token invalide"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Instance globale
telegram_notifier = TelegramNotifier()
