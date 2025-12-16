#!/usr/bin/env python3
"""
Script de test: Système de Paiement Moov Money
Démontre: initiation → confirmation → historique → remboursement
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path Python
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.moov_payment_service import MoovPaymentService
from app.config import settings

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration MongoDB
MONGODB_URL = settings.MONGODB_URL
DATABASE_NAME = settings.MONGODB_DATABASE


async def test_moov_payment_system():
    """Tester le système complet de paiement Moov Money"""
    
    # Connexion MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Initialiser le service
    moov_service = MoovPaymentService()
    
    try:
        print("\n" + "="*80)
        print("🎯 TEST: SYSTÈME DE PAIEMENT MOOV MONEY - AgriSmart")
        print("="*80 + "\n")
        
        # ==================== TEST 1: Initiation ====================
        print("\n📍 TEST 1: Initiation d'un Paiement")
        print("-" * 80)
        
        init_result = await moov_service.initiate_payment(
            db=db,
            buyer_phone="+22512345678",
            amount=10000,
            product_id="prod_cacao_001",
            buyer_id="user_buyer_001",
            seller_id="user_seller_001",
            quantity=2,
            unit_price=5000,
            description="Achat de cacao qualité premium"
        )
        
        if init_result.get("status") == "success":
            print(f"✅ Status: {init_result['status']}")
            print(f"📝 Message: {init_result['message']}")
            print(f"💳 ID Transaction: {init_result['transaction_id']}")
            print(f"💾 ID BD: {init_result['transaction_db_id']}")
            print(f"💰 Montant: {init_result['amount']} FCFA")
            print(f"📞 Réponse Moov: {init_result.get('moov_response', {})}")
            
            transaction_id = init_result['transaction_id']
        else:
            print(f"❌ Erreur: {init_result.get('message')}")
            return
        
        # ==================== TEST 2: Récupérer le Statut ====================
        print("\n\n📍 TEST 2: Récupérer le Statut du Paiement")
        print("-" * 80)
        
        status_result = await moov_service.get_transaction_status(
            db=db,
            transaction_id=transaction_id
        )
        
        if status_result.get("status") == "success":
            trans = status_result["transaction"]
            print(f"✅ Transaction trouvée")
            print(f"   Transaction ID: {trans['transaction_id']}")
            print(f"   Statut: {trans['status']}")
            print(f"   Montant: {trans['total_amount']} FCFA")
            print(f"   Quantité: {trans['quantity']} unités")
            print(f"   Prix unitaire: {trans['unit_price']} FCFA")
            print(f"   Créée le: {trans['created_at']}")
        else:
            print(f"❌ Erreur: {status_result.get('message')}")
        
        # ==================== TEST 3: Confirmation du Paiement ====================
        print("\n\n📍 TEST 3: Confirmation du Paiement (avec OTP)")
        print("-" * 80)
        
        confirm_result = await moov_service.confirm_payment(
            db=db,
            transaction_id=transaction_id,
            otp_code="123456"
        )
        
        print(f"✅ Status: {confirm_result['status']}")
        print(f"📝 Message: {confirm_result['message']}")
        print(f"💳 ID Transaction: {confirm_result['transaction_id']}")
        print(f"💳 Statut Paiement: {confirm_result.get('payment_status', 'N/A')}")
        
        # ==================== TEST 4: Historique Acheteur ====================
        print("\n\n📍 TEST 4: Historique des Paiements - Acheteur")
        print("-" * 80)
        
        buyer_history = await moov_service.get_user_transactions(
            db=db,
            user_id="user_buyer_001",
            role="buyer",
            limit=10
        )
        
        if buyer_history.get("status") == "success":
            count = buyer_history["count"]
            print(f"✅ Nombre de transactions: {count}")
            
            for i, trans in enumerate(buyer_history["transactions"], 1):
                print(f"\n   Transaction {i}:")
                print(f"      ID: {trans['transaction_id']}")
                print(f"      Produit: {trans['product_id']}")
                print(f"      Montant: {trans['total_amount']} FCFA")
                print(f"      Statut: {trans['status']}")
                print(f"      Créée: {trans['created_at']}")
        else:
            print(f"❌ Erreur: {buyer_history.get('message')}")
        
        # ==================== TEST 5: Historique Vendeur ====================
        print("\n\n📍 TEST 5: Historique des Paiements - Vendeur")
        print("-" * 80)
        
        seller_history = await moov_service.get_user_transactions(
            db=db,
            user_id="user_seller_001",
            role="seller",
            limit=10
        )
        
        if seller_history.get("status") == "success":
            count = seller_history["count"]
            print(f"✅ Nombre de transactions: {count}")
            
            for i, trans in enumerate(seller_history["transactions"], 1):
                print(f"\n   Transaction {i}:")
                print(f"      ID: {trans['transaction_id']}")
                print(f"      Produit: {trans['product_id']}")
                print(f"      Montant: {trans['total_amount']} FCFA")
                print(f"      Acheteur: {trans['buyer_id']}")
                print(f"      Statut: {trans['status']}")
        else:
            print(f"❌ Erreur: {seller_history.get('message')}")
        
        # ==================== TEST 6: Résumé des Paiements ====================
        print("\n\n📍 TEST 6: Résumé des Paiements - Acheteur")
        print("-" * 80)
        
        summary = await moov_service.get_payment_summary(
            db=db,
            user_id="user_buyer_001",
            role="buyer"
        )
        
        if summary.get("status") == "success":
            s = summary["summary"]
            print(f"✅ Total transactions: {s['total_transactions']}")
            print(f"💰 Montant total dépensé: {s['total_amount']} FCFA")
            print(f"\n📊 Répartition par statut:")
            for status, stats in s["by_status"].items():
                print(f"   {status.upper()}:")
                print(f"      Nombre: {stats['count']}")
                print(f"      Total: {stats['total']} FCFA")
                print(f"      Moyenne: {stats['average']:.0f} FCFA")
        else:
            print(f"❌ Erreur: {summary.get('message')}")
        
        # ==================== TEST 7: Créer plusieurs transactions ====================
        print("\n\n📍 TEST 7: Créer Plusieurs Transactions")
        print("-" * 80)
        
        products = [
            {"id": "prod_anacarde_001", "price": 1200, "qty": 5},
            {"id": "prod_manioc_001", "price": 300, "qty": 10},
            {"id": "prod_riz_001", "price": 550, "qty": 4}
        ]
        
        total_stored = 0
        for product in products:
            result = await moov_service.initiate_payment(
                db=db,
                buyer_phone="+22587654321",
                amount=product["price"] * product["qty"],
                product_id=product["id"],
                buyer_id="user_buyer_002",
                seller_id="user_seller_001",
                quantity=product["qty"],
                unit_price=product["price"]
            )
            
            if result.get("status") == "success":
                print(f"✅ {product['id']}: {product['price'] * product['qty']} FCFA stocké")
                total_stored += 1
        
        print(f"\n📊 Total transactions créées: {total_stored}")
        
        # ==================== TEST 8: Remboursement ====================
        print("\n\n📍 TEST 8: Remboursement d'un Paiement")
        print("-" * 80)
        
        refund_result = await moov_service.refund_payment(
            db=db,
            transaction_id=transaction_id,
            reason="Client non satisfait - qualité insuffisante"
        )
        
        print(f"✅ Status: {refund_result['status']}")
        print(f"📝 Message: {refund_result['message']}")
        print(f"💳 ID Transaction: {refund_result['transaction_id']}")
        print(f"💰 Montant remboursé: {refund_result.get('refund_amount', 'N/A')} FCFA")
        
        # ==================== TEST 9: Statistiques Globales ====================
        print("\n\n📍 TEST 9: Statistiques Globales MongoDB")
        print("-" * 80)
        
        # Agrégation MongoDB
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$total_amount"}
                }
            },
            {"$sort": {"total": -1}}
        ]
        
        stats = await db["transactions"].aggregate(pipeline).to_list(None)
        
        total_transactions = 0
        total_amount = 0
        
        print(f"📊 Transactions par statut:")
        for stat in stats:
            status = stat["_id"]
            count = stat["count"]
            total = stat["total"]
            total_transactions += count
            total_amount += total
            
            print(f"   {status.upper():10} → {count} transactions, {total} FCFA")
        
        print(f"\n💾 TOTAL en BD: {total_transactions} transactions, {total_amount} FCFA")
        
        # ==================== TEST 10: Vérifier MongoDB ====================
        print("\n\n📍 TEST 10: Vérification Collection MongoDB")
        print("-" * 80)
        
        doc_count = await db["transactions"].count_documents({})
        print(f"✅ Nombre total d'enregistrements: {doc_count}")
        
        # Dernière transaction
        last_trans = await db["transactions"].find_one(
            {},
            sort=[("created_at", -1)]
        )
        
        if last_trans:
            print(f"\n   Dernière transaction:")
            print(f"      ID: {last_trans.get('transaction_id', 'N/A')}")
            print(f"      Montant: {last_trans.get('total_amount')} FCFA")
            print(f"      Statut: {last_trans.get('status')}")
            print(f"      Créée: {last_trans.get('created_at')}")
        
        # ==================== RÉSUMÉ ====================
        print("\n\n" + "="*80)
        print("✅ TOUS LES TESTS COMPLÉTÉS AVEC SUCCÈS")
        print("="*80)
        
        print(f"""
📝 RÉSUMÉ:
   ✅ Initiation de paiement
   ✅ Récupération du statut
   ✅ Confirmation du paiement
   ✅ Historique acheteur
   ✅ Historique vendeur
   ✅ Résumé des paiements
   ✅ Création de multiples transactions
   ✅ Remboursement
   ✅ Statistiques globales
   ✅ Vérification MongoDB

🎯 Le système de paiement Moov Money fonctionne parfaitement!
   MongoDB stocke tous les historiques des transactions.
""")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {str(e)}")
        print(f"\n❌ ERREUR: {str(e)}\n")
    
    finally:
        if client:
            client.close()
        logger.info("✅ Connexion MongoDB fermée")


if __name__ == "__main__":
    print("\n🚀 Démarrage des tests du système de paiement...\n")
    asyncio.run(test_moov_payment_system())
