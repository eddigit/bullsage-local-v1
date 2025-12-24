"""
Script d'intégration du Pro Trader AI
"""

def integrate_pro_trader():
    server_path = "server.py"
    
    with open(server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà intégré
    if "pro_trader_routes" in content:
        print("✅ Pro Trader AI déjà intégré!")
        return
    
    # 1. Ajouter l'import après advanced_routes
    old_import = "ADVANCED_ROUTES_AVAILABLE = False"
    new_import = """ADVANCED_ROUTES_AVAILABLE = False

# Import du Pro Trader AI
try:
    from services.pro_trader_routes import pro_trader_router
    PRO_TRADER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Pro Trader AI non disponible: {e}")
    PRO_TRADER_AVAILABLE = False"""
    
    content = content.replace(old_import, new_import)
    
    # 2. Ajouter l'inclusion du router
    old_include = 'logger.info("✅ Routes avancées chargées")'
    new_include = '''logger.info("✅ Routes avancées chargées")

# Inclure Pro Trader AI si disponible
if PRO_TRADER_AVAILABLE:
    app.include_router(pro_trader_router)
    logger.info("🧠 Pro Trader AI chargé")'''
    
    content = content.replace(old_include, new_include)
    
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Pro Trader AI intégré avec succès!")
    print("   Endpoints disponibles:")
    print("   - GET /api/pro/scan - Scanner les meilleures opportunités")
    print("   - GET /api/pro/recommendation/{symbol} - Recommandation complète")
    print("   - GET /api/pro/quick/{symbol} - Analyse rapide")
    print("   - GET /api/pro/dashboard - Dashboard Pro")
    print("\n🔄 Redémarrez le serveur pour appliquer")

if __name__ == "__main__":
    integrate_pro_trader()
