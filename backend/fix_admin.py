"""Script pour diagnostiquer et réparer le compte admin"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def diagnose_and_fix():
    print("=" * 60)
    print("DIAGNOSTIC BULLSAGE")
    print("=" * 60)
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url:
        print("❌ ERREUR: MONGO_URL non défini dans .env")
        return
    
    print(f"\n📦 Database: {db_name}")
    print(f"🔗 MongoDB URL: {mongo_url[:30]}...")
    
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        # Test connexion
        await client.admin.command('ping')
        print("✅ Connexion MongoDB OK")
        
        db = client[db_name]
        
        # Compter les collections
        print("\n📊 STATISTIQUES:")
        users_count = await db.users.count_documents({})
        trades_count = await db.paper_trades.count_documents({})
        signals_count = await db.signals.count_documents({})
        
        print(f"   - Utilisateurs: {users_count}")
        print(f"   - Paper Trades: {trades_count}")
        print(f"   - Signaux: {signals_count}")
        
        # Lister les utilisateurs
        print("\n👤 UTILISATEURS:")
        users = await db.users.find({}, {'email': 1, 'name': 1, 'is_admin': 1, '_id': 0}).to_list(100)
        
        if not users:
            print("   ⚠️ AUCUN UTILISATEUR TROUVÉ!")
        else:
            for u in users:
                admin_badge = "🔑 ADMIN" if u.get('is_admin') else ""
                print(f"   - {u.get('email')} ({u.get('name')}) {admin_badge}")
        
        # Vérifier les admins
        admins = await db.users.find({'is_admin': True}).to_list(100)
        print(f"\n🔐 ADMINS: {len(admins)} compte(s) admin")
        
        if not admins:
            print("\n⚠️ AUCUN ADMIN TROUVÉ!")
            print("Voulez-vous promouvoir le premier utilisateur en admin? (Script automatique)")
            
            first_user = await db.users.find_one({})
            if first_user:
                await db.users.update_one(
                    {'id': first_user['id']},
                    {'$set': {'is_admin': True}}
                )
                print(f"✅ {first_user['email']} est maintenant admin!")
        
        client.close()
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_and_fix())
