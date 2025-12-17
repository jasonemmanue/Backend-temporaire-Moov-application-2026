from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_database
from app.core.dependencies import get_current_active_user
from app.models.user import UserResponse
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Récupère le profil de l'utilisateur connecté
    Utilisé pour obtenir le user_type et contrôler l'accès aux pages
    """
    try:
        # Convertir l'ObjectId en string pour la réponse
        user_data = {
            "_id": str(current_user["_id"]),
            "phone_number": current_user.get("phone_number"),
            "name": current_user.get("name"),
            "email": current_user.get("email"),
            "user_type": current_user.get("user_type"),
            "location": current_user.get("location"),
            "region": current_user.get("region"),
            "profile_picture": current_user.get("profile_picture"),
            "language": current_user.get("language", "fr"),
            "is_verified": current_user.get("is_verified", False),
            "status": current_user.get("status", "active"),
            "rating": current_user.get("rating", 0.0),
            "total_transactions": current_user.get("total_transactions", 0),
            "created_at": current_user.get("created_at"),
            "updated_at": current_user.get("updated_at")
        }

        return UserResponse(**user_data)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )
