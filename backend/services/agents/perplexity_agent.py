"""
Perplexity Agent - Recherche et News avec sources
"""
import httpx
from typing import Dict, Any
from .base_agent import BaseTradingAgent


class PerplexityAgent(BaseTradingAgent):
    """Agent utilisant l'API Perplexity pour la recherche avec sources"""
    
    async def _call_api(self, prompt: str) -> str:
        """Appel API Perplexity"""
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY manquante")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": f"Tu es {self.name}, expert en recherche d'actualités et news trading. "
                               "Cite toujours tes sources. Réponds en JSON valide."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extraire le contenu
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            
            raise ValueError(f"Réponse invalide Perplexity: {data}")
