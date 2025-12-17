# app/main.py
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Optional
import logging
from datetime import datetime

# Import nos modules
from app.config import settings
from app.database import mongodb, get_database

# Import des routeurs
from app.api import test as test_router
from app.api import blockchain as blockchain_router
from app.api import auth as auth_router
from app.api import payment as payment_router
from app.api import products as products_router  # <--- AJOUT IMPORTANT

# Import des modèles pour les autres endpoints restants dans main.py
from app.models import (
    ProductCreate, ProductUpdate, TransactionCreate,
    UserResponse, ProductResponse, TransactionResponse,
    MarketPriceResponse, WeatherResponse,
    UserType, ProductType, ProductStatus, TransactionStatus
)
from app.core.dependencies import get_current_active_user, get_current_user
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

# ============================================
# GESTION DU CYCLE DE VIE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info("🚀 Démarrage d'AgriSmart CI avec MongoDB...")
    
    try:
        await mongodb.connect()
        logger.info("✅ MongoDB connecté avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la connexion à MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de l'application...")
    await mongodb.disconnect()
    logger.info("✅ Application arrêtée proprement")

# ============================================
# APPLICATION FASTAPI
# ============================================

app = FastAPI(
    title="AgriSmart CI API",
    description="API Backend pour l'assistant agricole intelligent avec MongoDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# INCLUSION DES ROUTEURS
# ============================================

# C'est ici qu'on connecte les fichiers séparés
app.include_router(test_router.router)
app.include_router(blockchain_router.router)
app.include_router(auth_router.router)
app.include_router(payment_router.router)
app.include_router(products_router.router)  # <--- NOUVEAU: API Produits complète

# ============================================
# UTILITAIRES
# ============================================

def to_objectid(id_str: str) -> ObjectId:
    """Convertir un string en ObjectId MongoDB"""
    try:
        return ObjectId(id_str)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID invalide"
        )

def serialize_mongo_document(doc) -> dict:
    """Sérialiser un document MongoDB"""
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

# ============================================
# ENDPOINTS UTILISATEURS (Restants)
# ============================================
# Note: Idéalement, déplacez ces routes dans app/api/users.py plus tard

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_active_user)
):
    """Obtenir les informations de l'utilisateur connecté"""
    return UserResponse(**serialize_mongo_document(current_user))

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Obtenir les informations d'un utilisateur"""
    user = await db.users.find_one({"_id": to_objectid(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    return UserResponse(**serialize_mongo_document(user))

@app.get("/api/users", response_model=List[UserResponse])
async def get_users(
    user_type: Optional[UserType] = None,
    limit: int = 100,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Lister les utilisateurs avec filtres"""
    query = {}
    if user_type:
        query["user_type"] = user_type.value
    
    cursor = db.users.find(query).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return [UserResponse(**serialize_mongo_document(user)) for user in users]

# ============================================
# ENDPOINTS SANTÉ ET STATS
# ============================================

@app.get("/")
async def root():
    return {
        "message": "🌱 Bienvenue sur AgriSmart CI API avec MongoDB",
        "version": "1.0.0",
        "status": "operational",
        "database": "MongoDB",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}