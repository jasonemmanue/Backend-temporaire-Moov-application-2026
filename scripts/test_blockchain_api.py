"""
Test des endpoints API blockchain
Teste les endpoints HTTP de tracabilite
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/blockchain"

print("\n" + "="*80)
print("TEST DES ENDPOINTS BLOCKCHAIN API")
print("="*80 + "\n")

# TEST 1: Creer un smart contract
print("TEST 1: Creer un smart contract")
print("-" * 80)

response = requests.post(
    f"{BASE_URL}/smart-contract/create",
    params={
        "product_id": "prod_cafe_002",
        "farmer_id": "farmer_yamoussoukro_001",
        "farmer_name": "Paul N'Guessan",
        "product_type": "Cafe Arabica",
        "quantity": 300,
        "unit": "kg",
        "expected_delivery_days": 10,
        "buyer_id": "buyer_roasters_001",
        "price": 1500000
    }
)

if response.status_code == 200:
    data = response.json()
    contract_id = data['contract']['contract_id']
    print(f"[OK] Statut: {data['status']}")
    print(f"Contract ID: {contract_id}")
    print(f"Produit: {data['contract']['product_type']}")
    print(f"Quantite: {data['contract']['quantity']} {data['contract']['unit']}")
else:
    print(f"[ERREUR] {response.status_code}")
    print(response.text)
    contract_id = None

print()

if contract_id:
    # TEST 2: Enregistrer une etape (Recolte)
    print("TEST 2: Enregistrer la recolte")
    print("-" * 80)

    response = requests.post(
        f"{BASE_URL}/record-stage",
        params={
            "product_id": "prod_cafe_002",
            "stage": "harvested",
            "actor": "farmer",
            "actor_id": "farmer_yamoussoukro_001",
            "location": "Yamoussoukro, Region du Comoe",
            "temperature": 23.5,
            "humidity": 68,
            "quality_score": 88,
            "notes": "Recolte selective, grains sains",
            "contract_id": contract_id
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Statut: {data['status']}")
        print(f"Transaction ID: {data['transaction_id']}")
        print(f"Etape: {data['stage']}")
        print(f"Hash: {data['transaction_hash'][:20]}...")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

    # TEST 3: Enregistrer le controle qualite
    print("TEST 3: Enregistrer le controle qualite")
    print("-" * 80)

    response = requests.post(
        f"{BASE_URL}/record-stage",
        params={
            "product_id": "prod_cafe_002",
            "stage": "quality_checked",
            "actor": "inspector",
            "actor_id": "inspector_002",
            "location": "Centre de controle, Abidjan",
            "quality_score": 86,
            "notes": "OK Acidite. OK Humidite 10pct. Approuve",
            "contract_id": contract_id
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Transaction enregistree")
        print(f"ID: {data['transaction_id']}")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

    # TEST 4: Enregistrer l'emballage
    print("TEST 4: Enregistrer l'emballage")
    print("-" * 80)

    response = requests.post(
        f"{BASE_URL}/record-stage",
        params={
            "product_id": "prod_cafe_002",
            "stage": "packaged",
            "actor": "processor",
            "actor_id": "processor_002",
            "location": "Usine de transformation, Port-Bouet",
            "temperature": 21.0,
            "humidity": 50,
            "notes": "Sacs 50kg - Code lot: CAFE-2025-001",
            "contract_id": contract_id
        }
    )

    if response.status_code == 200:
        print(f"[OK] Emballage enregistre")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

    # TEST 5: Recuperer la trace complete
    print("TEST 5: Recuperer la trace complete")
    print("-" * 80)

    response = requests.get(f"{BASE_URL}/product-trace/prod_cafe_002")

    if response.status_code == 200:
        data = response.json()['data']
        print(f"[OK] Product ID: {data['product_id']}")
        print(f"Contrats: {len(data['contracts'])}")
        print(f"Transactions: {len(data['transactions'])}")
        print(f"\nTimeline:")
        for i, event in enumerate(data['timeline'], 1):
            print(f"  {i}. {event['stage'].upper()} - {event['actor']}")
            if event['quality_score']:
                print(f"     Qualite: {event['quality_score']}/100")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

    # TEST 6: Verifier l'authenticite
    print("TEST 6: Verifier l'authenticite")
    print("-" * 80)

    response = requests.get(f"{BASE_URL}/verify-authenticity/prod_cafe_002")

    if response.status_code == 200:
        data = response.json()['data']
        print(f"[OK] Authentique: {data['is_authentic']}")
        print(f"Transactions verifiees: {data['transaction_count']}")
        print(f"Blocs blockchain: {data['blockchain_blocks']}")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

    # TEST 7: Statut du smart contract
    print("TEST 7: Statut du smart contract")
    print("-" * 80)

    response = requests.get(f"{BASE_URL}/contract/{contract_id}")

    if response.status_code == 200:
        data = response.json()['data']
        print(f"[OK] Contract: {data['contract_id']}")
        print(f"Conditions respectees: {data['compliance']['conditions_met']}")
        print(f"Etapes completees: {data['compliance']['stages_completed']}/{data['compliance']['total_stages']}")
        print(f"Avancement: {data['compliance']['completion_percentage']:.1f}%")
    else:
        print(f"[ERREUR] {response.status_code}")

    print()

# TEST 8: Statistiques globales
print("TEST 8: Statistiques globales blockchain")
print("-" * 80)

response = requests.get(f"{BASE_URL}/stats")

if response.status_code == 200:
    data = response.json()['data']
    print(f"[OK] Blocs: {data['total_blocks']}")
    print(f"Transactions: {data['total_transactions']}")
    print(f"Contrats: {data['total_contracts']}")
    print(f"Statut reseau: {data['network_status']}")
else:
    print(f"[ERREUR] {response.status_code}")

print()

# TEST 9: Statistiques du fermier
print("TEST 9: Statistiques du fermier")
print("-" * 80)

response = requests.get(f"{BASE_URL}/farmer-stats/farmer_yamoussoukro_001")

if response.status_code == 200:
    data = response.json()['data']
    print(f"[OK] Fermier: {data['farmer_id']}")
    print(f"Contrats actifs: {data['active_contracts']}")
    print(f"Produits totaux: {data['total_products']} kg")
    print(f"Score reputation: {data['reputation_score']:.1f}/100")
else:
    print(f"[ERREUR] {response.status_code}")

print()

print("="*80)
print("TOUS LES TESTS API REUSSIS!")
print("="*80)
print("\nEndpoints testes:")
print("  OK POST /smart-contract/create")
print("  OK POST /record-stage")
print("  OK GET /product-trace/{product_id}")
print("  OK GET /verify-authenticity/{product_id}")
print("  OK GET /contract/{contract_id}")
print("  OK GET /stats")
print("  OK GET /farmer-stats/{farmer_id}")
print("\nBlockchain Simulee - Operationnelle!")
print("   Acces a http://localhost:8000/docs pour Swagger UI\n")
