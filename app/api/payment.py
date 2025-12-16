"""
API Endpoints pour les paiements Moov Money
Routes pour initier, confirmer, et gerer les transactions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.database import get_database
from app.services.moov_payment_service import MoovPaymentService
from app.schemas.payment import (
    InitiatePaymentRequest,
    ConfirmPaymentRequest,
    RefundPaymentRequest,
    MoovPaymentResponse,
    PaymentSummaryResponse,
    TransactionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["payment"])

# Initialiser le service Moov
moov_service = MoovPaymentService()


@router.post("/initiate", response_model=MoovPaymentResponse)
async def initiate_payment(
    request: InitiatePaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Initier un paiement Moov Money"""
    try:
        result = await moov_service.initiate_payment(
            db=db,
            buyer_phone=request.buyer_phone,
            amount=request.amount,
            product_id=request.product_id,
            buyer_id=request.buyer_id,
            seller_id=request.seller_id,
            quantity=request.quantity,
            unit_price=request.unit_price,
            description=request.description
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'initiation du paiement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=MoovPaymentResponse)
async def confirm_payment(
    request: ConfirmPaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Confirmer un paiement avec OTP"""
    try:
        result = await moov_service.confirm_payment(
            db=db,
            transaction_id=request.transaction_id,
            otp_code=request.otp_code
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Recuperer le statut d'un paiement"""
    try:
        result = await moov_service.get_transaction_status(
            db=db,
            transaction_id=transaction_id
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation du statut: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
async def get_transaction_history(
    user_id: str,
    role: str = Query(default="buyer", description="buyer ou seller"),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Recuperer l'historique des transactions d'un utilisateur"""
    try:
        result = await moov_service.get_user_transactions(
            db=db,
            user_id=user_id,
            role=role,
            limit=limit
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation de l'historique: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{user_id}")
async def get_payment_summary(
    user_id: str,
    role: str = Query(default="buyer", description="buyer ou seller"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Recuperer un resume des paiements d'un utilisateur"""
    try:
        result = await moov_service.get_payment_summary(
            db=db,
            user_id=user_id,
            role=role
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du calcul du resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund", response_model=MoovPaymentResponse)
async def refund_payment(
    request: RefundPaymentRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Effectuer un remboursement"""
    try:
        result = await moov_service.refund_payment(
            db=db,
            transaction_id=request.transaction_id,
            reason=request.reason
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du remboursement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/all-users")
async def get_all_transactions_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Recuperer les statistiques de tous les paiements (admin only)"""
    try:
        # Agregation MongoDB pour les statistiques globales
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$total_amount"},
                    "average": {"$avg": "$total_amount"}
                }
            }
        ]
        
        stats = await db["transactions"].aggregate(pipeline).to_list(None)
        
        # Transactions recentes
        recent = await db["transactions"].find(
            {}
        ).sort("created_at", -1).limit(10).to_list(None)
        
        # Convertir les ObjectId
        for trans in recent:
            trans["_id"] = str(trans["_id"])
            trans["created_at"] = trans["created_at"].isoformat()
            trans["updated_at"] = trans["updated_at"].isoformat()
        
        return {
            "status": "success",
            "statistics": {
                "by_status": stats,
                "recent_transactions": recent
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
