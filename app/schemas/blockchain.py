from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# --- Schémas utilisés par l'API ---

class ProductTraceRequest(BaseModel):
    """Schéma pour la création d'une trace (Entrée API)"""
    farmer_phone: str
    product_name: str
    product_type: str
    quantity: float
    location: Optional[str] = None
    harvest_date: Optional[datetime] = None

class ProductTraceResponse(BaseModel):
    """Schéma pour la réponse d'une trace (Sortie API)"""
    id: str
    farmer_phone: Optional[str] = None
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    quantity: Optional[float] = None
    location: Optional[str] = None
    harvest_date: Optional[datetime] = None
    created_at: datetime

class FarmerTracesResponse(BaseModel):
    """Schéma pour la liste des traces d'un fermier"""
    farmer_phone: str
    total_traces: int
    traces: List[ProductTraceResponse]

class BlockchainStatus(BaseModel):
    """Schéma pour le statut du système"""
    database: str
    collection: str
    total_traces: int
    status: str