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
from app.api import auth as auth_router  # <--- AJOUT IMPORTANT

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
app.include_router(auth_router.router)  # <--- ON BRANCHE L'AUTH ICI

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
# ENDPOINTS PRODUITS (Restants)
# ============================================

@app.post("/api/products", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Créer un nouveau produit (authentification requise)"""
    product_data = {
        "name": product.name,
        "product_type": product.product_type.value,
        "quantity": product.quantity,
        "price_per_kg": product.price_per_kg,
        "location": product.location,
        "description": product.description,
        "images": product.images,
        "owner_id": str(current_user["_id"]),
        "owner_phone": current_user["phone_number"],
        "owner_name": current_user["name"],
        "status": ProductStatus.AVAILABLE.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.products.insert_one(product_data)
    created_product = await db.products.find_one({"_id": result.inserted_id})
    return ProductResponse(**serialize_mongo_document(created_product))

@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    product_type: Optional[ProductType] = None,
    status: Optional[ProductStatus] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Lister les produits avec filtres"""
    query = {}
    if product_type:
        query["product_type"] = product_type.value
    if status:
        query["status"] = status.value
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if min_price is not None or max_price is not None:
        query["price_per_kg"] = {}
        if min_price is not None:
            query["price_per_kg"]["$gte"] = min_price
        if max_price is not None:
            query["price_per_kg"]["$lte"] = max_price
    
    cursor = db.products.find(query).sort("created_at", -1).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    return [ProductResponse(**serialize_mongo_document(product)) for product in products]

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Obtenir un produit spécifique"""
    product = await db.products.find_one({"_id": to_objectid(product_id)})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )
    return ProductResponse(**serialize_mongo_document(product))

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