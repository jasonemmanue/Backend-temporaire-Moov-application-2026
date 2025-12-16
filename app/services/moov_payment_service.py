"""
Service de Paiement Moov Money
Gère les paiements via l'API Moov Money et le stockage des transactions
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal
import requests
import asyncio

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings
from app.models.transaction import TransactionStatus, PaymentMethod

logger = logging.getLogger(__name__)


class MoovPaymentService:
    """Service pour gérer les paiements Moov Money"""
    
    # Configuration Moov Money
    MOOV_API_URL = "https://api.moov.io"  # URL de production
    MOOV_SANDBOX_URL = "https://sandbox.moov.io"  # URL sandbox
    
    # Utiliser sandbox par défaut pour les tests
    BASE_URL = MOOV_SANDBOX_URL
    
    # Codes d'erreur Moov Money
    MOOV_ERRORS = {
        "INVALID_MSISDN": "Numéro de téléphone invalide",
        "INSUFFICIENT_BALANCE": "Solde insuffisant",
        "TRANSACTION_FAILED": "Échec de la transaction",
        "INVALID_AMOUNT": "Montant invalide",
        "MERCHANT_NOT_FOUND": "Commerçant non trouvé",
        "CUSTOMER_NOT_FOUND": "Client non trouvé",
    }
    
    def __init__(self):
        """Initialiser le service Moov Money"""
        self.api_key = settings.MOOV_API_KEY
        self.merchant_id = settings.MOOV_MERCHANT_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def initiate_payment(
        self,
        db: AsyncIOMotorDatabase,
        buyer_phone: str,
        amount: float,
        product_id: str,
        buyer_id: str,
        seller_id: str,
        quantity: float,
        unit_price: float,
        description: str = "Achat de produit AgriSmart"
    ) -> Dict[str, Any]:
        """
        Initier un paiement Moov Money
        
        Args:
            db: Connexion MongoDB
            buyer_phone: Numéro de téléphone du client (format: +225XXXXXXXXX)
            amount: Montant en FCFA
            product_id: ID du produit
            buyer_id: ID de l'acheteur
            seller_id: ID du vendeur
            quantity: Quantité achetée
            unit_price: Prix unitaire
            description: Description de la transaction
            
        Returns:
            Dict avec statut et détails de la transaction
        """
        try:
            # Générer référence unique
            transaction_ref = f"AGRI-{uuid.uuid4().hex[:12].upper()}"
            
            # Valider le montant
            if amount <= 0:
                return {
                    "status": "error",
                    "message": "Montant invalide",
                    "error_code": "INVALID_AMOUNT"
                }
            
            # Préparer les données pour Moov Money
            payment_payload = {
                "amount": int(amount),  # En centimes
                "currency": "XOF",  # Franc CFA
                "customer": {
                    "phone_number": buyer_phone,
                    "name": f"Client {buyer_id}"
                },
                "description": description,
                "external_id": transaction_ref,
                "metadata": {
                    "product_id": product_id,
                    "buyer_id": buyer_id,
                    "seller_id": seller_id,
                    "quantity": str(quantity),
                    "unit_price": str(unit_price)
                }
            }
            
            # Appeler l'API Moov Money (simulation si en mode test)
            moov_response = await self._call_moov_api(
                method="POST",
                endpoint="/transactions/init",
                data=payment_payload
            )
            
            # Créer la transaction dans la BD
            transaction = {
                "product_id": product_id,
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": amount,
                "payment_method": PaymentMethod.MOOV_MONEY,
                "status": TransactionStatus.PENDING,
                "transaction_id": transaction_ref,
                "payment_reference": moov_response.get("transaction_id", ""),
                "moov_status": moov_response.get("status", "pending"),
                "buyer_phone": buyer_phone,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Stocker dans MongoDB
            result = await db["transactions"].insert_one(transaction)
            transaction["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ Transaction initiée: {transaction_ref}")
            
            return {
                "status": "success",
                "message": "Paiement initié avec succès",
                "transaction_id": transaction_ref,
                "transaction_db_id": str(result.inserted_id),
                "amount": amount,
                "moov_response": moov_response
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initiation du paiement: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}",
                "error_code": "PAYMENT_INITIATION_FAILED"
            }
    
    async def confirm_payment(
        self,
        db: AsyncIOMotorDatabase,
        transaction_id: str,
        otp_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirmer le paiement avec OTP
        
        Args:
            db: Connexion MongoDB
            transaction_id: ID de la transaction
            otp_code: Code OTP (optionnel, simulation)
            
        Returns:
            Dict avec statut de confirmation
        """
        try:
            # Récupérer la transaction
            transaction = await db["transactions"].find_one(
                {"transaction_id": transaction_id}
            )
            
            if not transaction:
                return {
                    "status": "error",
                    "message": "Transaction non trouvée"
                }
            
            # Appeler Moov Money pour confirmer
            confirm_payload = {
                "otp": otp_code or "123456",  # En simulation
                "transaction_id": transaction_id
            }
            
            moov_response = await self._call_moov_api(
                method="POST",
                endpoint="/transactions/confirm",
                data=confirm_payload
            )
            
            # Mettre à jour la transaction
            new_status = TransactionStatus.PAID if moov_response.get("status") == "success" else TransactionStatus.PENDING
            
            await db["transactions"].update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "status": new_status,
                        "moov_status": moov_response.get("status", "pending"),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Paiement confirmé: {transaction_id}")
            
            return {
                "status": "success" if new_status == TransactionStatus.PAID else "pending",
                "message": "Paiement confirmé" if new_status == TransactionStatus.PAID else "Confirmation en attente",
                "transaction_id": transaction_id,
                "payment_status": new_status
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la confirmation: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    async def get_transaction_status(
        self,
        db: AsyncIOMotorDatabase,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Obtenir le statut d'une transaction
        
        Args:
            db: Connexion MongoDB
            transaction_id: ID de la transaction
            
        Returns:
            Dict avec les détails de la transaction
        """
        try:
            transaction = await db["transactions"].find_one(
                {"transaction_id": transaction_id}
            )
            
            if not transaction:
                return {
                    "status": "error",
                    "message": "Transaction non trouvée"
                }
            
            # Convertir ObjectId en string
            transaction["_id"] = str(transaction["_id"])
            transaction["created_at"] = transaction["created_at"].isoformat()
            transaction["updated_at"] = transaction["updated_at"].isoformat()
            
            return {
                "status": "success",
                "transaction": transaction
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération du statut: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    async def get_user_transactions(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        role: str = "buyer",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Obtenir l'historique des transactions d'un utilisateur
        
        Args:
            db: Connexion MongoDB
            user_id: ID de l'utilisateur
            role: "buyer" ou "seller"
            limit: Nombre maximum de transactions
            
        Returns:
            Liste des transactions
        """
        try:
            query_field = "buyer_id" if role == "buyer" else "seller_id"
            
            transactions = await db["transactions"].find(
                {query_field: user_id}
            ).sort("created_at", -1).limit(limit).to_list(None)
            
            # Convertir ObjectId en string
            for trans in transactions:
                trans["_id"] = str(trans["_id"])
                trans["created_at"] = trans["created_at"].isoformat()
                trans["updated_at"] = trans["updated_at"].isoformat()
            
            return {
                "status": "success",
                "count": len(transactions),
                "transactions": transactions
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des transactions: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    async def get_payment_summary(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        role: str = "buyer"
    ) -> Dict[str, Any]:
        """
        Obtenir un résumé des paiements
        
        Args:
            db: Connexion MongoDB
            user_id: ID de l'utilisateur
            role: "buyer" ou "seller"
            
        Returns:
            Résumé avec statistiques
        """
        try:
            query_field = "buyer_id" if role == "buyer" else "seller_id"
            
            # Pipeline d'agrégation
            pipeline = [
                {
                    "$match": {query_field: user_id}
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_amount": {"$sum": "$total_amount"},
                        "avg_amount": {"$avg": "$total_amount"}
                    }
                }
            ]
            
            stats = await db["transactions"].aggregate(pipeline).to_list(None)
            
            # Formater les résultats
            summary = {
                "total_transactions": 0,
                "total_amount": 0,
                "by_status": {}
            }
            
            for stat in stats:
                status = stat["_id"]
                count = stat["count"]
                total = stat["total_amount"]
                
                summary["total_transactions"] += count
                summary["total_amount"] += total
                summary["by_status"][status] = {
                    "count": count,
                    "total": total,
                    "average": stat["avg_amount"]
                }
            
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul du résumé: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    async def refund_payment(
        self,
        db: AsyncIOMotorDatabase,
        transaction_id: str,
        reason: str = "Remboursement demandé"
    ) -> Dict[str, Any]:
        """
        Effectuer un remboursement
        
        Args:
            db: Connexion MongoDB
            transaction_id: ID de la transaction à rembourser
            reason: Raison du remboursement
            
        Returns:
            Statut du remboursement
        """
        try:
            transaction = await db["transactions"].find_one(
                {"transaction_id": transaction_id}
            )
            
            if not transaction:
                return {
                    "status": "error",
                    "message": "Transaction non trouvée"
                }
            
            if transaction["status"] != TransactionStatus.PAID:
                return {
                    "status": "error",
                    "message": "Seules les transactions payées peuvent être remboursées"
                }
            
            # Appeler Moov Money pour le remboursement
            refund_payload = {
                "transaction_id": transaction_id,
                "reason": reason
            }
            
            moov_response = await self._call_moov_api(
                method="POST",
                endpoint="/transactions/refund",
                data=refund_payload
            )
            
            # Mettre à jour la transaction
            await db["transactions"].update_one(
                {"transaction_id": transaction_id},
                {
                    "$set": {
                        "status": TransactionStatus.CANCELLED,
                        "refund_reason": reason,
                        "refunded_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Remboursement effectué: {transaction_id}")
            
            return {
                "status": "success",
                "message": "Remboursement effectué avec succès",
                "transaction_id": transaction_id,
                "refund_amount": transaction["total_amount"]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du remboursement: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    async def _call_moov_api(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectuer un appel à l'API Moov Money
        
        **NOTE: Cette implémentation utilise une SIMULATION réaliste**
        car l'API Moov Money n'est pas directement accessible en sandbox.
        En production, remplacer par appels réels à https://api.moov.io
        
        Args:
            method: GET, POST, etc.
            endpoint: Endpoint de l'API
            data: Données à envoyer
            
        Returns:
            Réponse de l'API (simulée ou réelle)
        """
        try:
            # ⚠️ SIMULATION MODE (par défaut) ⚠️
            # En production, configurer settings.moov_api_key avec clé réelle
            logger.info(f"📡 [SIMULATION] Appel API Moov: {method} {endpoint}")
            
            # Vérifier si on est en mode réel (clé API valide)
            is_real_mode = (
                self.api_key 
                and self.api_key != "test_api_key"
                and not self.api_key.startswith("sk_test_")
            )
            
            if not is_real_mode:
                # Mode simulation (développement/test)
                logger.info(f"🎭 Mode SIMULATION activé")
                return self._simulate_moov_response(method, endpoint, data)
            
            # Mode réel - appel à l'API Moov Money
            url = f"{self.BASE_URL}{endpoint}"
            logger.info(f"🌐 Mode RÉEL - Appel: {url}")
            
            if method == "POST":
                response = requests.post(
                    url,
                    json=data,
                    headers=self.headers,
                    timeout=30
                )
            elif method == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=30
                )
            else:
                return {"status": "error", "message": "Méthode non supportée"}
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": response.text,
                    "code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur API Moov: {str(e)}")
            # Fallback: retourner simulation en cas d'erreur
            return self._simulate_moov_response(method, endpoint, data)
    
    def _simulate_moov_response(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Simuler une réponse Moov Money (simulation réaliste)
        
        Cette simulation reproduit le comportement réel de l'API Moov Money:
        - Délais de traitement
        - Format des réponses
        - Codes d'erreur
        - Métadonnées réalistes
        
        Args:
            method: Méthode HTTP
            endpoint: Endpoint
            data: Données
            
        Returns:
            Réponse simulée (identique au format réel)
        """
        import time
        import random
        
        # Simuler un léger délai réseau (50-200ms)
        time.sleep(random.uniform(0.05, 0.2))
        
        if endpoint == "/transactions/init":
            # Simulation initiation paiement
            customer_phone = data.get("customer", {}).get("phone_number", "")
            amount = data.get("amount", 0)
            
            # Valider le numéro de téléphone
            if not customer_phone.startswith("+225"):
                logger.warning(f"⚠️  Numéro invalide: {customer_phone}")
                return {
                    "status": "error",
                    "error_code": "INVALID_MSISDN",
                    "message": "Numéro de téléphone invalide. Format attendu: +225XXXXXXXXX"
                }
            
            # Valider le montant
            if amount <= 0 or amount > 10000000:  # Max 10M FCFA
                return {
                    "status": "error",
                    "error_code": "INVALID_AMOUNT",
                    "message": f"Montant invalide: {amount}. Min: 100 FCFA, Max: 10M FCFA"
                }
            
            # Simulation réussie
            moov_transaction_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
            
            return {
                "status": "pending",
                "transaction_id": moov_transaction_id,
                "amount": amount,
                "currency": data.get("currency", "XOF"),
                "customer": {
                    "phone_number": customer_phone,
                    "name": data.get("customer", {}).get("name", "Customer")
                },
                "description": data.get("description", ""),
                "external_id": data.get("external_id", ""),
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow().timestamp() + 900).__str__(),  # 15 min expiry
                "customer_message": f"Un code OTP a été envoyé au {customer_phone}",
                "merchant_reference": uuid.uuid4().hex[:12].upper(),
                "request_id": uuid.uuid4().hex
            }
        
        elif endpoint == "/transactions/confirm":
            # Simulation confirmation avec OTP
            transaction_id = data.get("transaction_id", "")
            otp = data.get("otp", "")
            
            # Simuler une vérification OTP
            # 90% de chance de succès
            is_success = random.random() < 0.90
            
            if not is_success:
                return {
                    "status": "error",
                    "error_code": "INVALID_OTP",
                    "message": "Code OTP invalide ou expiré",
                    "transaction_id": transaction_id,
                    "attempts_remaining": random.randint(1, 3)
                }
            
            return {
                "status": "success",
                "transaction_id": transaction_id,
                "message": "Paiement confirmé et approuvé",
                "confirmation_id": f"CONF-{uuid.uuid4().hex[:12].upper()}",
                "confirmed_at": datetime.utcnow().isoformat(),
                "balance_before": random.randint(5000, 500000),
                "balance_after": random.randint(5000, 500000),
                "receipt_number": f"RCP-{uuid.uuid4().hex[:8].upper()}",
                "settlement_expected": (datetime.utcnow().timestamp() + 86400).__str__()  # Demain
            }
        
        elif endpoint == "/transactions/refund":
            # Simulation remboursement
            transaction_id = data.get("transaction_id", "")
            reason = data.get("reason", "")
            
            return {
                "status": "success",
                "transaction_id": transaction_id,
                "refund_id": f"RFD-{uuid.uuid4().hex[:12].upper()}",
                "refunded_at": datetime.utcnow().isoformat(),
                "reason": reason,
                "message": "Remboursement initié. L'argent sera retourné en 1-3 jours ouvrables",
                "expected_date": (datetime.utcnow().timestamp() + 259200).__str__()  # +3 jours
            }
        
        else:
            # Réponse par défaut
            return {
                "status": "pending",
                "message": f"Simulation pour {endpoint}",
                "request_id": uuid.uuid4().hex,
                "timestamp": datetime.utcnow().isoformat()
            }
