"""
Anthropic Agent - Claude
"""
import httpx
from typing import Dict, Any
from .base_agent import BaseTradingAgent


class AnthropicAgent(BaseTradingAgent):
    """Agent utilisant l'API Anthropic (Claude)"""
    
    async def _call_api(self, prompt: str) -> str:
        """Appel API Anthropic"""
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante")
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 1500,
            "messages": [
                {
                    "role": "user",
                    "content": f"Tu es {self.name}, expert en {self.role}. Réponds en JSON valide.\n\n{prompt}"
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extraire le contenu
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0]["text"]
            
            raise ValueError(f"Réponse invalide Anthropic: {data}")
