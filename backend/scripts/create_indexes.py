"""
Script de creation des index MongoDB pour Bull Sage
====================================================

Execute ce script pour creer tous les index necessaires pour optimiser
les performances des requetes.

Usage:
    python scripts/create_indexes.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent.parent / '.env')


async def create_indexes():
    """Cree tous les index MongoDB necessaires"""

    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'bullsage')

    if not mongo_url:
        print("ERREUR: MONGO_URL non configure")
        return False

    print("=" * 60)
    print("BULL SAGE - Creation des Index MongoDB")
    print("=" * 60)

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    indexes_created = 0
    errors = []

    # Liste des index a creer
    indexes = [
        # Collection: signals
        ("signals", [
            {"keys": [("user_id", 1)], "name": "idx_signals_user_id"},
            {"keys": [("created_at", -1)], "name": "idx_signals_created_at"},
            {"keys": [("status", 1)], "name": "idx_signals_status"},
            {"keys": [("user_id", 1), ("status", 1)], "name": "idx_signals_user_status"},
            {"keys": [("user_id", 1), ("created_at", -1)], "name": "idx_signals_user_created"},
            {"keys": [("webhook_acknowledged", 1)], "name": "idx_signals_webhook_ack"},
            {"keys": [("symbol", 1)], "name": "idx_signals_symbol"},
            {"keys": [("confidence", -1)], "name": "idx_signals_confidence"},
        ]),

        # Collection: trades (paper trading)
        ("trades", [
            {"keys": [("user_id", 1)], "name": "idx_trades_user_id"},
            {"keys": [("created_at", -1)], "name": "idx_trades_created_at"},
            {"keys": [("status", 1)], "name": "idx_trades_status"},
            {"keys": [("user_id", 1), ("status", 1)], "name": "idx_trades_user_status"},
            {"keys": [("symbol", 1)], "name": "idx_trades_symbol"},
        ]),

        # Collection: positions
        ("positions", [
            {"keys": [("user_id", 1)], "name": "idx_positions_user_id"},
            {"keys": [("market", 1)], "name": "idx_positions_market"},
            {"keys": [("status", 1)], "name": "idx_positions_status"},
            {"keys": [("user_id", 1), ("status", 1)], "name": "idx_positions_user_status"},
        ]),

        # Collection: trade_journal
        ("trade_journal", [
            {"keys": [("user_id", 1)], "name": "idx_journal_user_id"},
            {"keys": [("timestamp", -1)], "name": "idx_journal_timestamp"},
            {"keys": [("market", 1)], "name": "idx_journal_market"},
            {"keys": [("status", 1)], "name": "idx_journal_status"},
            {"keys": [("signal_id", 1)], "name": "idx_journal_signal_id"},
            {"keys": [("source", 1)], "name": "idx_journal_source"},
        ]),

        # Collection: webhook_logs
        ("webhook_logs", [
            {"keys": [("timestamp", -1)], "name": "idx_webhook_logs_timestamp"},
            {"keys": [("endpoint", 1)], "name": "idx_webhook_logs_endpoint"},
            {"keys": [("status", 1)], "name": "idx_webhook_logs_status"},
            {"keys": [("client_ip", 1)], "name": "idx_webhook_logs_ip"},
        ]),

        # Collection: users
        ("users", [
            {"keys": [("email", 1)], "name": "idx_users_email", "unique": True},
            {"keys": [("id", 1)], "name": "idx_users_id", "unique": True},
            {"keys": [("is_admin", 1)], "name": "idx_users_admin"},
        ]),

        # Collection: alerts
        ("alerts", [
            {"keys": [("user_id", 1)], "name": "idx_alerts_user_id"},
            {"keys": [("triggered", 1)], "name": "idx_alerts_triggered"},
            {"keys": [("symbol", 1)], "name": "idx_alerts_symbol"},
        ]),

        # Collection: strategies
        ("strategies", [
            {"keys": [("user_id", 1)], "name": "idx_strategies_user_id"},
        ]),

        # Collection: academy_progress
        ("academy_progress", [
            {"keys": [("user_id", 1)], "name": "idx_academy_user_id"},
            {"keys": [("module_id", 1)], "name": "idx_academy_module_id"},
            {"keys": [("user_id", 1), ("module_id", 1)], "name": "idx_academy_user_module"},
        ]),

        # Collection: chat_history
        ("chat_history", [
            {"keys": [("user_id", 1)], "name": "idx_chat_user_id"},
            {"keys": [("timestamp", -1)], "name": "idx_chat_timestamp"},
        ]),

        # Collection: auto_trades
        ("auto_trades", [
            {"keys": [("user_id", 1)], "name": "idx_auto_trades_user_id"},
            {"keys": [("status", 1)], "name": "idx_auto_trades_status"},
            {"keys": [("created_at", -1)], "name": "idx_auto_trades_created"},
        ]),

        # Collection: wallets
        ("wallets", [
            {"keys": [("user_id", 1)], "name": "idx_wallets_user_id"},
            {"keys": [("address", 1)], "name": "idx_wallets_address"},
        ]),

        # Collection: newsletter_logs
        ("newsletter_logs", [
            {"keys": [("sent_at", -1)], "name": "idx_newsletter_sent_at"},
        ]),
    ]

    for collection_name, collection_indexes in indexes:
        print(f"\n[{collection_name}]")
        collection = db[collection_name]

        for index_spec in collection_indexes:
            try:
                keys = index_spec["keys"]
                name = index_spec.get("name")
                unique = index_spec.get("unique", False)

                await collection.create_index(keys, name=name, unique=unique, background=True)
                print(f"  ✅ {name}")
                indexes_created += 1

            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    print(f"  ⏭️  {name} (existe deja)")
                else:
                    print(f"  ❌ {name}: {error_msg}")
                    errors.append(f"{collection_name}.{name}: {error_msg}")

    # Resume
    print("\n" + "=" * 60)
    print("RESUME")
    print("=" * 60)
    print(f"Index crees: {indexes_created}")
    print(f"Erreurs: {len(errors)}")

    if errors:
        print("\nErreurs:")
        for err in errors:
            print(f"  - {err}")

    # Afficher les index existants
    print("\n" + "=" * 60)
    print("INDEX EXISTANTS PAR COLLECTION")
    print("=" * 60)

    for collection_name, _ in indexes:
        try:
            existing = await db[collection_name].index_information()
            if len(existing) > 1:  # Plus que _id
                print(f"\n[{collection_name}]: {len(existing)} index")
                for idx_name, idx_info in existing.items():
                    if idx_name != "_id_":
                        print(f"  - {idx_name}")
        except Exception as e:
            pass

    client.close()
    return len(errors) == 0


if __name__ == "__main__":
    success = asyncio.run(create_indexes())
    sys.exit(0 if success else 1)
