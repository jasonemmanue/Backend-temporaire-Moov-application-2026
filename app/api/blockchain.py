"""
API endpoints pour la blockchain simulée et les smart contracts
Traçabilité des produits agricoles avec enregistrement des étapes clés
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
import logging

from app.database import get_database
from app.services.blockchain_simulation import BlockchainSimulationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain & Traçabilité"])

# Instance globale du service blockchain
blockchain_service = None


def get_blockchain_service(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Dépendance pour obtenir le service blockchain"""
    global blockchain_service
    if blockchain_service is None:
        blockchain_service = BlockchainSimulationService(db)
    return blockchain_service


@router.post("/smart-contract/create")
async def create_smart_contract(
    product_id: str = Query(..., description="ID du produit"),
    farmer_id: str = Query(..., description="ID du fermier"),
    farmer_name: str = Query(..., description="Nom du fermier"),
    product_type: str = Query(..., description="Type de produit (cacao, café, etc)"),
    quantity: float = Query(..., gt=0, description="Quantité"),
    unit: str = Query(..., description="Unité (kg, tonnes, etc)"),
    expected_delivery_days: int = Query(..., ge=1, description="Délai de livraison en jours"),
    buyer_id: Optional[str] = None,
    price: float = Query(0.0, ge=0, description="Prix en FCFA"),
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Crée un smart contract pour un produit agricole"""
    try:
        result = await service.create_smart_contract(
            product_id=product_id,
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            product_type=product_type,
            quantity=quantity,
            unit=unit,
            expected_delivery_days=expected_delivery_days,
            buyer_id=buyer_id,
            price=price
        )
        return result
    except Exception as e:
        logger.error(f"Error creating smart contract: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/record-stage")
async def record_product_stage(
    product_id: str = Query(..., description="ID du produit"),
    stage: str = Query(..., description="Étape (planted, harvested, shipped, delivered, sold)"),
    actor: str = Query(..., description="Acteur (farmer, inspector, transporter, buyer)"),
    actor_id: str = Query(..., description="ID de l'acteur"),
    location: str = Query(..., description="Localisation (ville, région)"),
    temperature: Optional[float] = Query(None, description="Température en °C"),
    humidity: Optional[float] = Query(None, description="Humidité en %"),
    quality_score: Optional[float] = Query(None, ge=0, le=100, description="Score de qualité 0-100"),
    notes: str = Query("", description="Notes supplémentaires"),
    contract_id: Optional[str] = Query(None, description="ID du smart contract associé"),
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Enregistre une étape du produit sur la blockchain"""
    try:
        result = await service.record_product_stage(
            product_id=product_id,
            stage=stage,
            actor=actor,
            actor_id=actor_id,
            location=location,
            temperature=temperature,
            humidity=humidity,
            quality_score=quality_score,
            notes=notes,
            contract_id=contract_id
        )
        return result
    except Exception as e:
        logger.error(f"Error recording product stage: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/product-trace/{product_id}")
async def get_product_trace(
    product_id: str,
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Récupère la trace complète d'un produit sur la blockchain"""
    try:
        trace = await service.get_product_trace(product_id)
        return {
            "status": "success",
            "data": trace
        }
    except Exception as e:
        logger.error(f"Error getting product trace: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-authenticity/{product_id}")
async def verify_product_authenticity(
    product_id: str,
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Vérifie l'authenticité d'un produit via la blockchain"""
    try:
        result = await service.verify_product_authenticity(product_id)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error verifying authenticity: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contract/{contract_id}")
async def get_contract_status(
    contract_id: str,
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Récupère le statut d'un smart contract"""
    try:
        status = await service.get_contract_status(contract_id)
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting contract status: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_blockchain_stats(
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Récupère les statistiques globales de la blockchain"""
    try:
        stats = await service.get_blockchain_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/farmer-stats/{farmer_id}")
async def get_farmer_statistics(
    farmer_id: str,
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Récupère les statistiques d'un fermier (contrats, pénalités, réputation)"""
    try:
        stats = await service.get_farmer_statistics(farmer_id)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting farmer stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/force-mine-block")
async def force_mine_block(
    service: BlockchainSimulationService = Depends(get_blockchain_service)
):
    """Force le minage d'un bloc (utile pour les tests)"""
    try:
        result = await service._mine_block()
        if result:
            return {
                "status": "success",
                "message": "Block mined successfully",
                "data": result
            }
        else:
            return {
                "status": "info",
                "message": "No pending transactions to mine"
            }
    except Exception as e:
        logger.error(f"Error mining block: {e}")
        raise HTTPException(status_code=400, detail=str(e))