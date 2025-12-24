"""Reset admin password script"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

async def reset_admin():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Nouveau mot de passe simple
    new_password = 'Admin123!'
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update les admins
    result = await db.users.update_many(
        {'is_admin': True},
        {'$set': {'password': hashed}}
    )
    
    print(f'Updated {result.modified_count} admin accounts')
    print(f'New password for all admins: Admin123!')
    
    # Liste les admins
    admins = await db.users.find({'is_admin': True}, {'email': 1, '_id': 0}).to_list(10)
    for admin in admins:
        print(f"Admin: {admin['email']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_admin())
