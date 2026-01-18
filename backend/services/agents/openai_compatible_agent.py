"""
OpenAI Compatible Agent
Supporte: Groq, DeepSeek, OpenRouter, xAI (Grok), Manus
"""
import httpx
from typing import Dict, Any
from .base_agent import BaseTradingAgent


class OpenAICompatibleAgent(BaseTradingAgent):
    """Agent utilisant l'API compatible OpenAI"""
    
    async def _call_api(self, prompt: str) -> str:
        """Appel API format OpenAI"""
        
        if not self.api_key:
            raise ValueError(f"API key manquante pour {self.provider}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Headers spéciaux pour OpenRouter
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://bullsagetrader.com"
            headers["X-Title"] = "Bull Sage Council"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": f"Tu es {self.name}, expert en {self.role} pour le trading. "
                               f"Réponds toujours en JSON valide."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1500
        }
        
        url = f"{self.base_url}/chat/completions"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extraire le contenu
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            
            raise ValueError(f"Réponse invalide de {self.provider}: {data}")
