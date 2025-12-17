# app/models/product.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum

from app.models.user import PyObjectId

class ProductType(str, Enum):
    COCOA = "cocoa"           # Cacao
    CASHEW = "cashew"         # Anacarde
    CASSAVA = "cassava"       # Manioc
    COFFEE = "coffee"         # Café
    RICE = "rice"             # Riz
    CORN = "corn"             # Maïs
    VEGETABLE = "vegetable"   # Légumes
    FRUIT = "fruit"           # Fruits
    PLANTAIN = "plantain"     # Banane plantain
    YAMS = "yams"             # Igname
    PEANUT = "peanut"         # Arachide
    COTTON = "cotton"         # Coton
    OTHER = "other"           # Autre

class ProductStatus(str, Enum):
    AVAILABLE = "available"      # Disponible à la vente
    RESERVED = "reserved"       # Réservé
    SOLD = "sold"              # Vendu
    HARVESTED = "harvested"    # Récolté (pas encore en vente)

class QualityGrade(str, Enum):
    GRADE_A = "A"      # Meilleure qualité
    GRADE_B = "B"      # Bonne qualité
    GRADE_C = "C"      # Qualité standard
    ORGANIC = "organic" # Biologique

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nom du produit")
    product_type: ProductType = Field(..., description="Type de produit")
    description: Optional[str] = Field(None, max_length=500, description="Description du produit")
    quantity: float = Field(..., gt=0, description="Quantité en kg")
    unit_price: float = Field(..., gt=0, description="Prix par kg en FCFA")
    location: str = Field(..., min_length=2, max_length=100, description="Lieu de production")
    harvest_date: Optional[datetime] = Field(None, description="Date de récolte")
    quality_grade: Optional[QualityGrade] = Field(QualityGrade.GRADE_B, description="Grade de qualité")

class ProductCreate(ProductBase):
    """Schéma pour créer un nouveau produit"""
    pass

class ProductUpdate(BaseModel):
    """Schéma pour mettre à jour un produit (tous les champs optionnels)"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    status: Optional[ProductStatus] = None
    quality_grade: Optional[QualityGrade] = None

class ProductResponse(BaseModel):
    """Schéma de réponse pour un produit"""
    id: str
    name: str
    product_type: str
    description: Optional[str] = None
    quantity: float
    unit_price: float
    location: str
    harvest_date: Optional[datetime] = None
    quality_grade: str
    owner_id: str
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    status: str
    views: int = 0
    favorite_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}