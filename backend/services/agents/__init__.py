"""
Bull Sage Council - Agents Factory
"""
from .base_agent import BaseTradingAgent
from .openai_compatible_agent import OpenAICompatibleAgent
from .anthropic_agent import AnthropicAgent
from .perplexity_agent import PerplexityAgent


def create_agent(config: dict) -> BaseTradingAgent:
    """
    Factory pour créer l'agent approprié selon le provider.
    
    Providers supportés:
    - groq: Llama (gratuit, rapide)
    - deepseek: DeepSeek Chat (très économique)
    - openrouter: Multi-modèles (Mixtral, GPT-4, etc.)
    - xai: Grok (sentiment X/Twitter)
    - manus: Manus-1 (stratégie)
    - anthropic: Claude (fondamental)
    - perplexity: Sonar (news avec sources)
    """
    provider = config.get("provider", "").lower()
    
    if provider == "anthropic":
        return AnthropicAgent(config)
    
    elif provider == "perplexity":
        return PerplexityAgent(config)
    
    else:
        # Groq, DeepSeek, OpenRouter, xAI, Manus utilisent l'API compatible OpenAI
        return OpenAICompatibleAgent(config)


__all__ = [
    "BaseTradingAgent",
    "OpenAICompatibleAgent",
    "AnthropicAgent",
    "PerplexityAgent",
    "create_agent"
]
