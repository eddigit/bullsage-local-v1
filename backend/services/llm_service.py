"""
LLM Service - Compatible wrapper to replace emergentintegrations
Uses OpenAI API directly for local deployment
"""
import os
import logging
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Get API key from environment
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')


class UserMessage:
    """Simple message wrapper for compatibility"""
    def __init__(self, text: str):
        self.text = text


class LlmChat:
    """
    Compatible LLM Chat wrapper that uses OpenAI API directly.
    Replaces emergentintegrations.llm.chat.LlmChat
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.session_id = session_id
        self.system_message = system_message or "Tu es un assistant IA expert en trading et marchés financiers."
        self.model = "gpt-4o"
        self.provider = "openai"
        self.messages = []
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Add system message to conversation
        if self.system_message:
            self.messages.append({
                "role": "system",
                "content": self.system_message
            })
    
    def with_model(self, provider: str, model: str) -> 'LlmChat':
        """Set the model to use"""
        self.provider = provider
        self.model = model
        return self
    
    async def send_message(self, message: UserMessage) -> str:
        """Send a message and get a response"""
        try:
            # Add user message
            self.messages.append({
                "role": "user",
                "content": message.text
            })
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract response text
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info(f"LLM response received ({len(assistant_message)} chars)")
            return assistant_message
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            # Return a fallback response
            return f"Désolé, une erreur s'est produite lors de l'analyse. Erreur: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.messages = []
        if self.system_message:
            self.messages.append({
                "role": "system",
                "content": self.system_message
            })


# Alternative simpler function for one-shot queries
async def get_ai_response(
    prompt: str,
    system_message: str = "Tu es un assistant IA expert en trading et marchés financiers.",
    model: str = "gpt-4o",
    api_key: Optional[str] = None
) -> str:
    """
    Simple one-shot AI query function
    """
    try:
        client = AsyncOpenAI(api_key=api_key or OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"Erreur IA: {str(e)}"


# Cache pour les traductions (évite de retraduire les mêmes textes)
_translation_cache = {}

async def translate_to_french(texts: list[dict], fields: list[str] = ["title", "summary"]) -> list[dict]:
    """
    Traduit une liste de textes de l'anglais vers le français.
    Utilise un cache pour éviter les traductions redondantes.
    
    Args:
        texts: Liste de dictionnaires contenant les textes à traduire
        fields: Liste des clés à traduire dans chaque dictionnaire
    
    Returns:
        Liste de dictionnaires avec les textes traduits
    """
    if not texts:
        return texts
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Préparer les textes à traduire (non cachés)
        texts_to_translate = []
        for item in texts:
            for field in fields:
                text = item.get(field, "")
                if text and text not in _translation_cache:
                    texts_to_translate.append(text)
        
        # Si tous les textes sont cachés, retourner directement
        if texts_to_translate:
            # Créer le prompt de traduction batch
            batch_text = "\n---\n".join(texts_to_translate[:20])  # Limiter à 20 textes
            
            prompt = f"""Traduis les textes suivants de l'anglais vers le français de manière naturelle et professionnelle.
Garde le même ton journalistique et financier.
Retourne UNIQUEMENT les traductions, séparées par "---" (exactement comme l'entrée).
Ne rajoute aucun commentaire.

Textes à traduire:
{batch_text}"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Modèle plus rapide pour les traductions
                messages=[
                    {"role": "system", "content": "Tu es un traducteur professionnel spécialisé dans la finance et les marchés. Tu traduis de l'anglais vers le français."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            translations = response.choices[0].message.content.split("---")
            translations = [t.strip() for t in translations]
            
            # Mettre en cache les traductions
            for i, original in enumerate(texts_to_translate[:len(translations)]):
                if i < len(translations):
                    _translation_cache[original] = translations[i]
        
        # Appliquer les traductions (depuis le cache)
        result = []
        for item in texts:
            new_item = item.copy()
            for field in fields:
                text = item.get(field, "")
                if text and text in _translation_cache:
                    new_item[field] = _translation_cache[text]
            result.append(new_item)
        
        logger.info(f"Traduit {len(texts_to_translate)} textes en français")
        return result
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        # En cas d'erreur, retourner les textes originaux
        return texts
