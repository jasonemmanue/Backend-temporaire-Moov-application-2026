"""
Service de Blockchain simulée pour la traçabilité des produits agricoles AgriSmart
Simulation réaliste avec smart contracts pour enregistrer les étapes clés
(Récolte, vente, livraison) - pas d'intégration réelle avec Ethereum
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
import random
from motor.motor_asyncio import AsyncIOMotorDatabase


class ProductStage(str, Enum):
    """Étapes du cycle de vie d'un produit agricole"""
    PLANTED = "planted"  # Semis
    GROWING = "growing"  # En croissance
    HARVESTED = "harvested"  # Récolté
    QUALITY_CHECKED = "quality_checked"  # Contrôle qualité
    PROCESSED = "processed"  # Traité
    PACKAGED = "packaged"  # Emballé
    SHIPPED = "shipped"  # Expédié
    IN_TRANSIT = "in_transit"  # En transit
    DELIVERED = "delivered"  # Livré
    SOLD = "sold"  # Vendu


class TransactionType(str, Enum):
    """Types de transactions blockchain"""
    SMART_CONTRACT = "smart_contract"
    PAYMENT = "payment"
    TRANSFER = "transfer"
    VERIFICATION = "verification"
    QUALITY_ASSURANCE = "quality_assurance"


class BlockchainTransaction:
    """Représente une transaction dans la blockchain"""
    
    def __init__(
        self,
        tx_id: str,
        product_id: str,
        stage: ProductStage,
        actor: str,
        actor_id: str,
        location: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        quality_score: Optional[float] = None,
        notes: str = "",
        tx_type: TransactionType = TransactionType.SMART_CONTRACT
    ):
        self.tx_id = tx_id
        self.product_id = product_id
        self.stage = stage
        self.actor = actor
        self.actor_id = actor_id
        self.location = location
        self.temperature = temperature
        self.humidity = humidity
        self.quality_score = quality_score
        self.notes = notes
        self.tx_type = tx_type
        self.timestamp = datetime.utcnow()
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calcule le hash SHA-256 de la transaction"""
        data = {
            "tx_id": self.tx_id,
            "product_id": self.product_id,
            "stage": self.stage,
            "actor": self.actor,
            "timestamp": str(self.timestamp),
        }
        hash_obj = hashlib.sha256(json.dumps(data, sort_keys=True).encode())
        return hash_obj.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "product_id": self.product_id,
            "stage": self.stage,
            "actor": self.actor,
            "actor_id": self.actor_id,
            "location": self.location,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "quality_score": self.quality_score,
            "notes": self.notes,
            "tx_type": self.tx_type,
            "timestamp": self.timestamp.isoformat(),
            "hash": self.hash
        }


class Block:
    """Représente un bloc dans la blockchain"""
    
    def __init__(
        self,
        block_index: int,
        transactions: List[BlockchainTransaction],
        previous_hash: str = "0" * 64,
        nonce: int = 0
    ):
        self.block_index = block_index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = datetime.utcnow()
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calcule le hash du bloc"""
        data = {
            "block_index": self.block_index,
            "previous_hash": self.previous_hash,
            "timestamp": str(self.timestamp),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce
        }
        hash_obj = hashlib.sha256(json.dumps(data, sort_keys=True).encode())
        return hash_obj.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_index": self.block_index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "hash": self.hash
        }


class SmartContract:
    """Smart contract pour la traçabilité des produits"""
    
    def __init__(
        self,
        contract_id: str,
        product_id: str,
        farmer_id: str,
        farmer_name: str,
        product_type: str,
        quantity: float,
        unit: str,
        expected_delivery_date: datetime,
        buyer_id: Optional[str] = None,
        price: float = 0.0,
        temperature_range: tuple = (15, 25),
        humidity_range: tuple = (40, 70)
    ):
        self.contract_id = contract_id
        self.product_id = product_id
        self.farmer_id = farmer_id
        self.farmer_name = farmer_name
        self.product_type = product_type
        self.quantity = quantity
        self.unit = unit
        self.expected_delivery_date = expected_delivery_date
        self.buyer_id = buyer_id
        self.price = price
        self.temperature_range = temperature_range
        self.humidity_range = humidity_range
        self.created_at = datetime.utcnow()
        self.status = "active"
        self.stages_completed: List[str] = []
        self.conditions_met = True
        self.penalties = 0.0
        self.contract_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Hash unique du contrat"""
        data = {
            "contract_id": self.contract_id,
            "product_id": self.product_id,
            "farmer_id": self.farmer_id,
            "created_at": str(self.created_at)
        }
        hash_obj = hashlib.sha256(json.dumps(data, sort_keys=True).encode())
        return hash_obj.hexdigest()
    
    def verify_conditions(
        self,
        stage: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        quality_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Vérifie les conditions du smart contract"""
        violations = []
        
        if temperature is not None:
            if not (self.temperature_range[0] <= temperature <= self.temperature_range[1]):
                violations.append(f"Temperature {temperature}°C out of range {self.temperature_range}")
                self.penalties += 100.0
        
        if humidity is not None:
            if not (self.humidity_range[0] <= humidity <= self.humidity_range[1]):
                violations.append(f"Humidity {humidity}% out of range {self.humidity_range}")
                self.penalties += 100.0
        
        if quality_score is not None:
            if quality_score < 70:
                violations.append(f"Quality score {quality_score}/100 below minimum 70")
                self.penalties += 200.0
        
        if stage == "delivered":
            if datetime.utcnow() > self.expected_delivery_date:
                late_days = (datetime.utcnow() - self.expected_delivery_date).days
                penalty = 50.0 * late_days
                violations.append(f"Delivered {late_days} days late")
                self.penalties += penalty
        
        self.conditions_met = len(violations) == 0
        
        return {
            "conditions_met": self.conditions_met,
            "violations": violations,
            "penalties": self.penalties,
            "stage": stage
        }
    
    def mark_stage_completed(self, stage: str):
        """Marque une étape comme complétée"""
        if stage not in self.stages_completed:
            self.stages_completed.append(stage)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "product_id": self.product_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "product_type": self.product_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "expected_delivery_date": self.expected_delivery_date.isoformat(),
            "buyer_id": self.buyer_id,
            "price": self.price,
            "temperature_range": self.temperature_range,
            "humidity_range": self.humidity_range,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "stages_completed": self.stages_completed,
            "conditions_met": self.conditions_met,
            "penalties": self.penalties,
            "contract_hash": self.contract_hash
        }


class BlockchainSimulationService:
    """Service de simulation blockchain pour la traçabilité des produits"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.blocks: List[Block] = []
        self.pending_transactions: List[BlockchainTransaction] = []
        self.smart_contracts: Dict[str, SmartContract] = {}
        self.genesis_block = self._create_genesis_block()
        self.blocks.append(self.genesis_block)
    
    def _create_genesis_block(self) -> Block:
        """Crée le bloc genesis"""
        genesis_tx = BlockchainTransaction(
            tx_id="genesis_tx_001",
            product_id="genesis",
            stage="planted",
            actor="system",
            actor_id="system",
            location="AgriSmart Network",
            notes="Genesis block - Network initialization"
        )
        return Block(
            block_index=0,
            transactions=[genesis_tx],
            previous_hash="0" * 64
        )
    
    async def create_smart_contract(
        self,
        product_id: str,
        farmer_id: str,
        farmer_name: str,
        product_type: str,
        quantity: float,
        unit: str,
        expected_delivery_days: int,
        buyer_id: Optional[str] = None,
        price: float = 0.0
    ) -> Dict[str, Any]:
        """Crée un smart contract pour un produit"""
        contract_id = f"SC-{product_id}-{int(time.time())}"
        expected_delivery = datetime.utcnow() + timedelta(days=expected_delivery_days)
        
        contract = SmartContract(
            contract_id=contract_id,
            product_id=product_id,
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            product_type=product_type,
            quantity=quantity,
            unit=unit,
            expected_delivery_date=expected_delivery,
            buyer_id=buyer_id,
            price=price
        )
        
        self.smart_contracts[contract_id] = contract
        
        await self.db.smart_contracts.insert_one({
            **contract.to_dict(),
            "created_at": datetime.utcnow()
        })
        
        return {
            "status": "success",
            "message": "Smart contract created",
            "contract_id": contract_id,
            "contract": contract.to_dict()
        }
    
    async def record_product_stage(
        self,
        product_id: str,
        stage: str,
        actor: str,
        actor_id: str,
        location: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        quality_score: Optional[float] = None,
        notes: str = "",
        contract_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enregistre une étape du produit sur la blockchain"""
        tx_id = f"TX-{product_id}-{stage}-{int(time.time() * 1000)}"
        
        transaction = BlockchainTransaction(
            tx_id=tx_id,
            product_id=product_id,
            stage=stage,
            actor=actor,
            actor_id=actor_id,
            location=location,
            temperature=temperature,
            humidity=humidity,
            quality_score=quality_score,
            notes=notes
        )
        
        self.pending_transactions.append(transaction)
        
        verification_result = None
        if contract_id and contract_id in self.smart_contracts:
            contract = self.smart_contracts[contract_id]
            contract.mark_stage_completed(stage)
            verification_result = contract.verify_conditions(
                stage=stage,
                temperature=temperature,
                humidity=humidity,
                quality_score=quality_score
            )
        
        if len(self.pending_transactions) >= 5:
            await self._mine_block()
        
        await self.db.blockchain_transactions.insert_one({
            **transaction.to_dict(),
            "contract_id": contract_id,
            "block_index": len(self.blocks) - 1
        })
        
        return {
            "status": "success",
            "message": "Product stage recorded on blockchain",
            "transaction_id": tx_id,
            "transaction_hash": transaction.hash,
            "stage": stage,
            "verification": verification_result,
            "block_index": len(self.blocks) - 1
        }
    
    async def _mine_block(self):
        """Mine un nouveau bloc"""
        if not self.pending_transactions:
            return
        
        previous_block = self.blocks[-1]
        new_block = Block(
            block_index=len(self.blocks),
            transactions=self.pending_transactions.copy(),
            previous_hash=previous_block.hash
        )
        
        new_block.hash = new_block._calculate_hash()
        
        self.blocks.append(new_block)
        
        await self.db.blockchain_blocks.insert_one(new_block.to_dict())
        
        self.pending_transactions = []
        
        return {
            "status": "success",
            "block_index": new_block.block_index,
            "block_hash": new_block.hash,
            "transactions_count": len(new_block.transactions)
        }
    
    async def get_product_trace(self, product_id: str) -> Dict[str, Any]:
        """Récupère la trace complète d'un produit"""
        contracts = []
        for c in self.smart_contracts.values():
            if c.product_id == product_id:
                contracts.append(c.to_dict())
        
        transactions = await self.db.blockchain_transactions.find(
            {"product_id": product_id}
        ).sort("timestamp", -1).to_list(None)
        
        # Convertir les ObjectId en strings
        clean_transactions = []
        for tx in transactions:
            clean_tx = dict(tx)
            if "_id" in clean_tx:
                clean_tx["_id"] = str(clean_tx["_id"])
            clean_transactions.append(clean_tx)
        
        trace = {
            "product_id": product_id,
            "contracts": contracts,
            "transactions": clean_transactions,
            "timeline": await self._build_timeline(product_id),
            "authenticity": {
                "is_authentic": True,
                "verification_date": datetime.utcnow().isoformat(),
                "blockchain_blocks": len(self.blocks)
            }
        }
        
        return trace
    
    async def _build_timeline(self, product_id: str) -> List[Dict[str, Any]]:
        """Construit la timeline des événements"""
        transactions = await self.db.blockchain_transactions.find(
            {"product_id": product_id}
        ).sort("timestamp", 1).to_list(None)
        
        timeline = []
        for tx in transactions:
            timeline.append({
                "stage": tx.get("stage"),
                "actor": tx.get("actor"),
                "location": tx.get("location"),
                "timestamp": tx.get("timestamp"),
                "temperature": tx.get("temperature"),
                "humidity": tx.get("humidity"),
                "quality_score": tx.get("quality_score"),
                "notes": tx.get("notes")
            })
        
        return timeline
    
    async def verify_product_authenticity(self, product_id: str) -> Dict[str, Any]:
        """Vérifie l'authenticité d'un produit"""
        transactions = await self.db.blockchain_transactions.find(
            {"product_id": product_id}
        ).to_list(None)
        
        if not transactions:
            return {
                "product_id": product_id,
                "is_authentic": False,
                "reason": "Product not found on blockchain"
            }
        
        integrity_check = True
        for tx in transactions:
            if not tx.get("hash"):
                integrity_check = False
                break
        
        return {
            "product_id": product_id,
            "is_authentic": integrity_check,
            "transaction_count": len(transactions),
            "first_recorded": transactions[0].get("timestamp") if transactions else None,
            "last_recorded": transactions[-1].get("timestamp") if transactions else None,
            "stages": [tx.get("stage") for tx in transactions],
            "blockchain_blocks": len(self.blocks)
        }
    
    async def get_contract_status(self, contract_id: str) -> Dict[str, Any]:
        """Récupère le statut d'un smart contract"""
        if contract_id not in self.smart_contracts:
            contract_data = await self.db.smart_contracts.find_one(
                {"contract_id": contract_id}
            )
            if not contract_data:
                return {"error": "Contract not found"}
            return contract_data
        
        contract = self.smart_contracts[contract_id]
        status = contract.to_dict()
        
        status["compliance"] = {
            "conditions_met": contract.conditions_met,
            "total_penalties": contract.penalties,
            "stages_completed": len(contract.stages_completed),
            "total_stages": len(ProductStage),
            "completion_percentage": (len(contract.stages_completed) / len(ProductStage)) * 100
        }
        
        return status
    
    async def get_blockchain_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la blockchain"""
        total_transactions = await self.db.blockchain_transactions.count_documents({})
        total_contracts = await self.db.smart_contracts.count_documents({})
        
        total_penalties = sum(
            c.penalties for c in self.smart_contracts.values()
        )
        
        return {
            "total_blocks": len(self.blocks),
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "total_contracts": total_contracts,
            "total_penalties": total_penalties,
            "network_status": "operational",
            "last_block_mined": self.blocks[-1].timestamp.isoformat() if self.blocks else None,
            "genesis_block": self.genesis_block.hash,
            "current_block": self.blocks[-1].hash if self.blocks else None
        }
    
    async def get_farmer_statistics(self, farmer_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'un fermier"""
        contracts = [
            c for c in self.smart_contracts.values()
            if c.farmer_id == farmer_id
        ]
        
        total_products = sum(c.quantity for c in contracts)
        completed_contracts = sum(
            1 for c in contracts if c.status == "completed"
        )
        total_penalties = sum(c.penalties for c in contracts)
        
        return {
            "farmer_id": farmer_id,
            "total_contracts": len(contracts),
            "completed_contracts": completed_contracts,
            "active_contracts": len([c for c in contracts if c.status == "active"]),
            "total_products": total_products,
            "total_penalties": total_penalties,
            "average_penalty": total_penalties / len(contracts) if contracts else 0,
            "reputation_score": max(0, 100 - min(total_penalties / 10, 100))
        }
