"""
Schémas Pydantic pour les paiements Moov Money
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TransactionStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class InitiatePaymentRequest(BaseModel):
    """Requête pour initier un paiement"""
    buyer_phone: str = Field(..., description="Numéro de téléphone (format: +225XXXXXXXXX)")
    amount: float = Field(..., gt=0, description="Montant en FCFA")
    product_id: str = Field(..., description="ID du produit")
    buyer_id: str = Field(..., description="ID de l'acheteur")
    seller_id: str = Field(..., description="ID du vendeur")
    quantity: float = Field(..., gt=0, description="Quantité achetée")
    unit_price: float = Field(..., gt=0, description="Prix unitaire")
    description: Optional[str] = Field(
        default="Achat de produit AgriSmart",
        description="Description de la transaction"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "buyer_phone": "+22512345678",
            "amount": 10000,
            "product_id": "prod_123",
            "buyer_id": "user_456",
            "seller_id": "user_789",
            "quantity": 2,
            "unit_price": 5000,
            "description": "Achat de cacao qualité premium"
        }
    })


class ConfirmPaymentRequest(BaseModel):
    """Requête pour confirmer un paiement"""
    transaction_id: str = Field(..., description="ID de la transaction")
    otp_code: Optional[str] = Field(
        default=None,
        description="Code OTP reçu par SMS (optionnel pour tests)"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "transaction_id": "AGRI-ABC123DEF456",
            "otp_code": "123456"
        }
    })


class RefundPaymentRequest(BaseModel):
    """Requête pour rembourser un paiement"""
    transaction_id: str = Field(..., description="ID de la transaction à rembourser")
    reason: Optional[str] = Field(
        default="Remboursement demandé",
        description="Raison du remboursement"
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "transaction_id": "AGRI-ABC123DEF456",
            "reason": "Produit non reçu"
        }
    })


class TransactionResponse(BaseModel):
    """Reponse avec details d'une transaction"""
    transaction_id: str
    product_id: str
    buyer_id: str
    seller_id: str
    quantity: float
    unit_price: float
    total_amount: float
    status: TransactionStatusEnum
    payment_method: str
    payment_reference: Optional[str] = None
    buyer_phone: Optional[str] = None
    moov_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    id: Optional[str] = Field(None, alias="_id")
    
    model_config = ConfigDict(populate_by_name=True)


class PaymentHistoryResponse(BaseModel):
    """Réponse avec historique des paiements"""
    transaction_id: str
    product_id: str
    amount: float
    status: TransactionStatusEnum
    created_at: datetime
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    
    model_config = ConfigDict()


class PaymentSummaryResponse(BaseModel):
    """Résumé des paiements par utilisateur"""
    total_transactions: int
    total_amount: float
    by_status: Dict[str, Dict[str, Any]]
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_transactions": 15,
            "total_amount": 150000,
            "by_status": {
                "paid": {
                    "count": 10,
                    "total": 100000,
                    "average": 10000
                },
                "pending": {
                    "count": 3,
                    "total": 30000,
                    "average": 10000
                },
                "cancelled": {
                    "count": 2,
                    "total": 20000,
                    "average": 10000
                }
            }
        }
    })


class MoovPaymentResponse(BaseModel):
    """Réponse générique d'une opération de paiement"""
    status: str = Field(..., description="Status: success, error, pending")
    message: str = Field(..., description="Message descriptif")
    transaction_id: Optional[str] = None
    transaction_db_id: Optional[str] = None
    amount: Optional[float] = None
    error_code: Optional[str] = None
    moov_response: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "success",
            "message": "Paiement initié avec succès",
            "transaction_id": "AGRI-ABC123DEF456",
            "transaction_db_id": "507f1f77bcf86cd799439011",
            "amount": 10000,
            "moov_response": {
                "status": "pending",
                "transaction_id": "MOOV-XYZ789ABC123"
            }
        }
    })


class TransactionHistoryRequest(BaseModel):
    """Requête pour récupérer l'historique des transactions"""
    user_id: str = Field(..., description="ID de l'utilisateur")
    role: str = Field(
        default="buyer",
        description="Role: buyer ou seller"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Nombre maximum de transactions"
    )


class TransactionStatistics(BaseModel):
    """Statistiques des transactions"""
    total_count: int
    total_amount: float
    pending_count: int
    pending_amount: float
    paid_count: int
    paid_amount: float
    cancelled_count: int
    cancelled_amount: float
    average_transaction: float
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_count": 25,
            "total_amount": 250000,
            "pending_count": 5,
            "pending_amount": 50000,
            "paid_count": 18,
            "paid_amount": 180000,
            "cancelled_count": 2,
            "cancelled_amount": 20000,
            "average_transaction": 10000
        }
    })
