"""
Script d'intégration des routes avancées
À exécuter UNE SEULE FOIS pour ajouter le router avancé au serveur
"""

import re

def integrate_advanced_routes():
    server_path = "server.py"
    
    # Lire le fichier
    with open(server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà intégré
    if "advanced_routes" in content:
        print("✅ Les routes avancées sont déjà intégrées!")
        return
    
    # 1. Ajouter l'import après les autres imports de services
    import_line = "from services.llm_service import LlmChat, UserMessage"
    new_import = """from services.llm_service import LlmChat, UserMessage

# Import des routes avancées (avec gestion d'erreur)
try:
    from services.advanced_routes import advanced_router
    ADVANCED_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Routes avancées non disponibles: {e}")
    ADVANCED_ROUTES_AVAILABLE = False"""
    
    content = content.replace(import_line, new_import)
    
    # 2. Ajouter l'inclusion du router avant le mount des fichiers statiques
    include_line = "app.include_router(api_router)"
    new_include = """app.include_router(api_router)

# Inclure les routes avancées si disponibles
if ADVANCED_ROUTES_AVAILABLE:
    app.include_router(advanced_router)
    logger.info("✅ Routes avancées chargées")"""
    
    content = content.replace(include_line, new_include)
    
    # Sauvegarder
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Routes avancées intégrées avec succès!")
    print("   - Import ajouté avec gestion d'erreur")
    print("   - Router inclus dans l'application")
    print("\n🔄 Redémarrez le serveur pour appliquer les changements")

if __name__ == "__main__":
    integrate_advanced_routes()
