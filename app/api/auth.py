from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_database
from app.schemas.auth import RegisterRequest, VerifyOTPRequest, LoginRequest, TokenResponse
from app.models.user import UserCreate, UserInDB, UserResponse, UserType
from app.core.otp_service import create_otp, verify_otp, send_otp_sms
from app.core.security import create_access_token
from bson import ObjectId
from datetime import datetime
import logging

# Configuration du logger pour voir les erreurs dans le terminal
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Inscription d'un nouvel utilisateur avec envoi d'OTP"""
    
    # 1. Vérifier si l'utilisateur existe déjà
    existing_user = await db.users.find_one({"phone_number": request.phone_number})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce numéro est déjà enregistré"
        )
    
    try:
        # 2. Préparer les données de l'utilisateur
        # On convertit le user_type (str) en Enum pour la validation, 
        # puis model_dump le remettra en string grâce à use_enum_values=True
        user_create = UserCreate(
            phone_number=request.phone_number,
            name=request.name,
            user_type=UserType[request.user_type.upper()], # Ex: "producer" -> UserType.PRODUCER
            location=request.location
        )
        
        # Convertir en dictionnaire pour MongoDB
        user_data = user_create.model_dump()
        
        # Ajouter les champs systèmes
        user_data.update({
            "is_verified": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # 3. Insérer dans MongoDB
        result = await db.users.insert_one(user_data)
        
        # 4. Générer et envoyer l'OTP
        otp_code = await create_otp(db, request.phone_number)
        await send_otp_sms(request.phone_number, otp_code)
        
        return {
            "message": "Code de vérification envoyé par SMS",
            "phone_number": request.phone_number,
            "user_id": str(result.inserted_id)
        }

    except KeyError:
        # Si le type d'utilisateur est invalide (ex: "Alien")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Type d'utilisateur invalide (producer, buyer, both)"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

# ============================================================================
# 🔥 MODIFIÉ : Retourner le token + les données utilisateur (user_type inclus)
# ============================================================================
@router.post("/verify-otp")
async def verify_otp_code(request: VerifyOTPRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Vérification du code OTP et connexion"""
    
    # 1. Vérifier le code OTP
    is_valid = await verify_otp(db, request.phone_number, request.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide ou expiré"
        )
    
    # 2. Récupérer et mettre à jour l'utilisateur
    user = await db.users.find_one_and_update(
        {"phone_number": request.phone_number},
        {
            "$set": {
                "is_verified": True,
                "updated_at": datetime.utcnow()
            }
        },
        return_document=True
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # 3. Créer le token JWT
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    # ===== MODIFICATION : Préparer les données utilisateur pour le retour =====
    # Convertir l'ObjectId en string pour la sérialisation JSON
    user["_id"] = str(user["_id"])
    
    # Supprimer les champs sensibles si présents (mot de passe, etc.)
    user.pop("hashed_password", None)
    
    # Log pour debug (optionnel)
    logger.info(f"✅ Connexion réussie - User: {user['name']} - Type: {user.get('user_type', 'N/A')}")
    
    # ===== RETOUR : Token JWT + Données utilisateur complètes =====
    # IMPORTANT : Inclut user_type, name, phone_number, location, etc.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user  # ← CRITIQUE : Contient toutes les infos dont user_type
    }

@router.post("/login")
async def login(request: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Connexion avec envoi d'OTP"""
    
    # 1. Vérifier si l'utilisateur existe
    user = await db.users.find_one({"phone_number": request.phone_number})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé. Veuillez vous inscrire."
        )
    
    # 2. Vérifier si l'utilisateur est actif
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # 3. Générer et envoyer l'OTP
    otp_code = await create_otp(db, request.phone_number)
    await send_otp_sms(request.phone_number, otp_code)
    
    return {
        "message": "Code de vérification envoyé par SMS",
        "phone_number": request.phone_number
    }