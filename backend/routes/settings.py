from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..core.config import db
from ..core.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.put("/trading-level")
async def update_trading_level(level: str, current_user: dict = Depends(get_current_user)):
    """Update user's trading level"""
    valid_levels = ["beginner", "intermediate", "advanced"]
    if level not in valid_levels:
        return {"error": f"Invalid level. Must be one of: {valid_levels}"}

    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"trading_level": level}}
    )
    return {"trading_level": level}


# ==================== BACKUP / RESTORE ====================

class SettingsBackup(BaseModel):
    settings: Dict[str, Any]
    description: Optional[str] = None


@router.post("/backup")
async def create_settings_backup(
    backup: Optional[SettingsBackup] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a backup of current user settings.
    If settings dict is provided, use that; otherwise snapshot the current user config.
    """
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Fields to backup
    backup_fields = [
        "trading_level", "preferences", "watchlist",
        "paper_balance", "onboarding_completed"
    ]
    snapshot = {k: user.get(k) for k in backup_fields if k in user}

    if backup and backup.settings:
        snapshot.update(backup.settings)

    backup_entry = {
        "user_id": current_user["id"],
        "settings": snapshot,
        "description": backup.description if backup else "Sauvegarde automatique",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.settings_backups.insert_one(backup_entry)
    backup_entry.pop("_id", None)

    return {
        "success": True,
        "message": "Sauvegarde créée",
        "backup": backup_entry
    }


@router.get("/backups")
async def list_settings_backups(current_user: dict = Depends(get_current_user)):
    """List all settings backups for the current user."""
    backups = await db.settings_backups.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)

    return {"backups": backups}


@router.post("/restore")
async def restore_settings(
    created_at: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Restore settings from a specific backup (identified by created_at timestamp).
    Creates a new backup of current settings before restoring.
    """
    # Find the backup
    backup = await db.settings_backups.find_one(
        {"user_id": current_user["id"], "created_at": created_at},
        {"_id": 0}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable")

    # Create safety backup before restoring
    current_user_data = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    backup_fields = ["trading_level", "preferences", "watchlist", "paper_balance", "onboarding_completed"]
    current_snapshot = {k: current_user_data.get(k) for k in backup_fields if k in current_user_data}

    await db.settings_backups.insert_one({
        "user_id": current_user["id"],
        "settings": current_snapshot,
        "description": "Sauvegarde auto avant restauration",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Restore
    settings_to_restore = backup.get("settings", {})
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": settings_to_restore}
    )

    return {
        "success": True,
        "message": "Paramètres restaurés avec succès",
        "restored_from": created_at
    }
