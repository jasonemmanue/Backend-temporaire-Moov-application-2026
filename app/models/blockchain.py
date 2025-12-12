from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

class ProductTrace(BaseModel):
    """Modèle pour la traçabilité blockchain (MongoDB)"""
    # ... champs ...
    product_ref: Optional[str] = None
    farmer_id: str
    blockchain_product_id: int
    ipfs_cid: str
    tx_hash: str
    block_number: Optional[int] = None
    metadata: Dict[str, Any] = {}
    status: str = "registered"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # CORRECTION : Nouvelle syntaxe de configuration Pydantic v2
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
    )

class BlockchainEvent(BaseModel):
    """Modèle pour les événements blockchain"""
    event_name: str
    tx_hash: str
    block_number: int
    data: Dict[str, Any] = {}
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)