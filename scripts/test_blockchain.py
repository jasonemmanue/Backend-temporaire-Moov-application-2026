#!/usr/bin/env python3
"""
Script de test pour la simulation blockchain et les smart contracts
Teste la traçabilité complète d'un produit agricole
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.blockchain_simulation import BlockchainSimulationService


async def test_blockchain_simulation():
    """Test complet du système blockchain simulé"""
    
    # Connexion MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.agrismart_db
    
    # Initialiser le service
    blockchain = BlockchainSimulationService(db)
    
    print("\n" + "="*80)
    print("🔗 TEST BLOCKCHAIN SIMULATION - TRAÇABILITÉ PRODUITS AGRICOLES")
    print("="*80 + "\n")
    
    # TEST 1: Créer un smart contract
    print("📋 TEST 1: Création d'un smart contract")
    print("-" * 80)
    
    contract_result = await blockchain.create_smart_contract(
        product_id="prod_cacao_001",
        farmer_id="farmer_abidjan_001",
        farmer_name="Jean Kouadio",
        product_type="Cacao Fermenté",
        quantity=500,
        unit="kg",
        expected_delivery_days=7,
        buyer_id="buyer_export_001",
        price=2500000  # FCFA
    )
    
    print(f"✅ Status: {contract_result['status']}")
    print(f"📜 Contract ID: {contract_result['contract']['contract_id']}")
    print(f"🌾 Produit: {contract_result['contract']['product_type']}")
    print(f"📦 Quantité: {contract_result['contract']['quantity']} {contract_result['contract']['unit']}")
    print(f"💰 Prix: {contract_result['contract']['price']} FCFA")
    print(f"📅 Livraison attendue: {contract_result['contract']['expected_delivery_date']}\n")
    
    contract_id = contract_result['contract']['contract_id']
    
    # TEST 2: Enregistrer le semis (Planted)
    print("📋 TEST 2: Enregistrement du semis")
    print("-" * 80)
    
    stage_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="planted",
        actor="farmer",
        actor_id="farmer_abidjan_001",
        location="Abidjan, Région du Goh",
        temperature=22.5,
        humidity=65,
        notes="Semis effectué avec variété Criollo",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {stage_result['transaction_id']}")
    print(f"📍 Étape: {stage_result['stage']}")
    print(f"🔐 Hash: {stage_result['transaction_hash'][:16]}...\n")
    
    # TEST 3: Récolte
    print("📋 TEST 3: Enregistrement de la récolte")
    print("-" * 80)
    
    harvest_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="harvested",
        actor="farmer",
        actor_id="farmer_abidjan_001",
        location="Abidjan, Ferme Kouadio",
        temperature=24.0,
        humidity=70,
        quality_score=85,
        notes="Récolte manuelle, cacaoyers sains",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {harvest_result['transaction_id']}")
    print(f"📍 Étape: {harvest_result['stage']}")
    print(f"⭐ Score de qualité: 85/100\n")
    
    # TEST 4: Contrôle qualité
    print("📋 TEST 4: Contrôle qualité")
    print("-" * 80)
    
    qc_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="quality_checked",
        actor="inspector",
        actor_id="inspector_001",
        location="Centre de contrôle, Abidjan",
        quality_score=82,
        notes="✓ Teneur en humidité: 7%. ✓ Pas de défauts. ✓ Prêt pour l'exportation",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {qc_result['transaction_id']}")
    print(f"📍 Étape: {qc_result['stage']}")
    print(f"⭐ Score final: 82/100\n")
    
    # TEST 5: Conditionnement
    print("📋 TEST 5: Conditionnement et emballage")
    print("-" * 80)
    
    pack_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="packaged",
        actor="processor",
        actor_id="processor_001",
        location="Usine de transformation, Port de Abidjan",
        temperature=20.0,
        humidity=45,
        notes="Emballage: 50 sacs de 10kg. Cachetage OK",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {pack_result['transaction_id']}")
    print(f"📍 Étape: {pack_result['stage']}\n")
    
    # TEST 6: Expédition
    print("📋 TEST 6: Expédition")
    print("-" * 80)
    
    ship_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="shipped",
        actor="transporter",
        actor_id="transporter_001",
        location="Port autonome de Abidjan",
        temperature=18.0,
        humidity=50,
        notes="Conteneur 40' - Navire MV AGRISHIP - Destination: Rotterdam",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {ship_result['transaction_id']}")
    print(f"📍 Étape: {ship_result['stage']}\n")
    
    # TEST 7: En transit
    print("📋 TEST 7: En transit")
    print("-" * 80)
    
    transit_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="in_transit",
        actor="shipping_company",
        actor_id="shipping_001",
        location="Océan Atlantique, Lat: 10.5N, Long: 25.3W",
        temperature=15.0,
        humidity=55,
        notes="En route. Jour 3 de 14. Tous les paramètres normaux",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {transit_result['transaction_id']}")
    print(f"📍 Étape: {transit_result['stage']}\n")
    
    # TEST 8: Livraison
    print("📋 TEST 8: Livraison")
    print("-" * 80)
    
    delivery_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="delivered",
        actor="buyer",
        actor_id="buyer_export_001",
        location="Port de Rotterdam, Pays-Bas",
        temperature=12.0,
        humidity=50,
        quality_score=80,
        notes="✓ Livraison dans les délais. ✓ Intégrité confirmée. ✓ Accepté",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {delivery_result['transaction_id']}")
    print(f"📍 Étape: {delivery_result['stage']}")
    print(f"⭐ Qualité à livraison: 80/100\n")
    
    # TEST 9: Vente
    print("📋 TEST 9: Vente au détaillant")
    print("-" * 80)
    
    sold_result = await blockchain.record_product_stage(
        product_id="prod_cacao_001",
        stage="sold",
        actor="retailer",
        actor_id="retailer_choco_001",
        location="Amsterdam, Manufacture de chocolat premium",
        quality_score=80,
        notes="Utilisation: Chocolat 70% Cacao. Batch de 200 tablettes premium",
        contract_id=contract_id
    )
    
    print(f"✅ Transaction ID: {sold_result['transaction_id']}")
    print(f"📍 Étape: {sold_result['stage']}\n")
    
    # Force mine un bloc
    print("📋 TEST 10: Minage du bloc blockchain")
    print("-" * 80)
    
    mine_result = await blockchain._mine_block()
    if mine_result:
        print(f"✅ Bloc miné!")
        print(f"📦 Index: {mine_result['block_index']}")
        print(f"🔐 Hash: {mine_result['block_hash'][:16]}...")
        print(f"📝 Transactions: {mine_result['transactions_count']}\n")
    
    # TEST 11: Récupérer la trace complète
    print("📋 TEST 11: Récupération de la trace complète")
    print("-" * 80)
    
    trace = await blockchain.get_product_trace("prod_cacao_001")
    
    print(f"📦 Product ID: {trace['product_id']}")
    print(f"📜 Smart Contracts: {len(trace['contracts'])}")
    print(f"📝 Transactions enregistrées: {len(trace['transactions'])}")
    print(f"\n🔗 Timeline complète:")
    
    for i, event in enumerate(trace['timeline'], 1):
        print(f"  {i}. {event['stage'].upper()} - {event['actor']} @ {event['location']}")
        if event['quality_score']:
            print(f"     ⭐ Qualité: {event['quality_score']}/100")
        if event['temperature']:
            print(f"     🌡️ Température: {event['temperature']}°C")
    
    print()
    
    # TEST 12: Vérifier l'authenticité
    print("📋 TEST 12: Vérification d'authenticité")
    print("-" * 80)
    
    auth = await blockchain.verify_product_authenticity("prod_cacao_001")
    
    print(f"✅ Authentique: {auth['is_authentic']}")
    print(f"📝 Transactions vérifiées: {auth['transaction_count']}")
    print(f"🔗 Blocs blockchain: {auth['blockchain_blocks']}")
    print(f"📅 Premier enregistrement: {auth['first_recorded']}")
    print(f"📅 Dernier enregistrement: {auth['last_recorded']}\n")
    
    # TEST 13: Statut du smart contract
    print("📋 TEST 13: Statut du smart contract")
    print("-" * 80)
    
    contract_status = await blockchain.get_contract_status(contract_id)
    
    print(f"📜 Contract: {contract_status['contract_id']}")
    print(f"✅ Conditions respectées: {contract_status['compliance']['conditions_met']}")
    print(f"📍 Étapes complétées: {contract_status['compliance']['stages_completed']}/{contract_status['compliance']['total_stages']}")
    print(f"📊 Avancement: {contract_status['compliance']['completion_percentage']:.1f}%")
    print(f"💰 Pénalités totales: {contract_status['compliance']['total_penalties']} FCFA\n")
    
    # TEST 14: Statistiques du fermier
    print("📋 TEST 14: Statistiques du fermier")
    print("-" * 80)
    
    farmer_stats = await blockchain.get_farmer_statistics("farmer_abidjan_001")
    
    print(f"👨‍🌾 Fermier: {farmer_stats['farmer_id']}")
    print(f"📜 Contrats actifs: {farmer_stats['active_contracts']}")
    print(f"✅ Contrats complétés: {farmer_stats['completed_contracts']}")
    print(f"📦 Produits totaux: {farmer_stats['total_products']} kg")
    print(f"💰 Pénalités: {farmer_stats['total_penalties']} FCFA")
    print(f"⭐ Score de réputation: {farmer_stats['reputation_score']:.1f}/100\n")
    
    # TEST 15: Statistiques blockchain
    print("📋 TEST 15: Statistiques globales blockchain")
    print("-" * 80)
    
    stats = await blockchain.get_blockchain_stats()
    
    print(f"🔗 Blocs: {stats['total_blocks']}")
    print(f"📝 Transactions: {stats['total_transactions']}")
    print(f"⏳ Transactions en attente: {stats['pending_transactions']}")
    print(f"📜 Contrats totaux: {stats['total_contracts']}")
    print(f"💰 Pénalités totales système: {stats['total_penalties']} FCFA")
    print(f"✅ Statut réseau: {stats['network_status']}")
    print(f"🔐 Genesis block: {stats['genesis_block'][:16]}...")
    print(f"🔐 Bloc courant: {stats['current_block'][:16]}...\n")
    
    print("="*80)
    print("✅ TOUS LES TESTS RÉUSSIS!")
    print("="*80)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(test_blockchain_simulation())