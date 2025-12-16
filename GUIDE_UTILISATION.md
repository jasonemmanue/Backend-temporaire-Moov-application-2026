# 📘 GUIDE COMPLET D'UTILISATION - AGRISMART

## Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Installation et Démarrage](#installation-et-démarrage)
3. [Architecture du Système](#architecture-du-système)
4. [Fonctionnement des Modules](#fonctionnement-des-modules)
5. [Exemples d'Utilisation](#exemples-dutilisation)
6. [Tests et Validation](#tests-et-validation)
7. [Dépannage](#dépannage)
8. [Déploiement](#déploiement)

---

## Vue d'ensemble

### Qu'est-ce que AgriSmart?

**AgriSmart** est une plateforme de traçabilité agricole blockchain qui intègre:
- **Système de Paiement**: Moov Money pour les transactions
- **Blockchain Simulation**: Pour enregistrer les étapes des produits
- **Smart Contracts**: Pour appliquer les conditions de livraison
- **Réputation**: Scoring automatique des fermiers

### Cas d'usage

```
FERMIER              ACHETEUR
   |                    |
   |-- Récolte         |
   |-- Qualité check   |
   |                    |-- Paiement initié
   |-- Emballage       |-- OTP confirmé
   |-- Expédition      |
   |-- En transit      |
   |-- Livraison ----> |
   |                    |-- Vérifier authenticité
   |-- Vente finalisée |
```

Chaque étape est enregistrée sur la blockchain avec:
- 📍 Localisation
- 🌡️ Température
- 💧 Humidité
- ⭐ Score de qualité
- ⏰ Timestamp immuable

---

## Installation et Démarrage

### Prérequis

```
✅ Python 3.13+
✅ MongoDB (Atlas Cloud ou Local)
✅ pip (gestionnaire de packages)
✅ Uvicorn (serveur ASGI)
```

### Installation Rapide

#### 1. Cloner le projet
```bash
cd "C:\Users\Admin\OneDrive - ENSEA\Documents\Ingrid\Moov\AgriSmart"
```

#### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

Packages essentiels:
```
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
pydantic==2.5.0
pymongo==4.6.0
africastalking==1.3.1
python-dotenv==1.0.0
```

#### 3. Configuration (fichier .env)
```env
# Base de données MongoDB
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/agrismart

# Africa's Talking (SMS)
AT_API_KEY=votre_cle_api
AT_USERNAME=votre_username
AT_SENDER_ID=AgriSmart

# Serveur
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

#### 4. Démarrer le serveur
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Résultat attendu:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 5. Accéder à l'API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Architecture du Système

### Structure des Dossiers

```
AgriSmart/
├── app/
│   ├── api/                    # Endpoints REST
│   │   ├── payment.py          # Paiement Moov Money (8 endpoints)
│   │   ├── blockchain.py       # Blockchain (7 endpoints)
│   │   └── ...
│   ├── services/               # Logique métier
│   │   ├── moov_payment_service.py
│   │   ├── blockchain_simulation.py
│   │   └── ...
│   ├── models/                 # Modèles MongoDB
│   │   ├── product.py
│   │   ├── transaction.py
│   │   ├── blockchain.py
│   │   └── ...
│   ├── schemas/                # Validation Pydantic
│   │   ├── payment.py
│   │   ├── product.py
│   │   └── ...
│   ├── core/                   # Configuration
│   │   ├── dependencies.py
│   │   ├── security.py
│   │   └── ...
│   ├── main.py                 # Application FastAPI
│   ├── config.py               # Configuration
│   └── database.py             # Connexion MongoDB
├── scripts/                    # Scripts de test
│   ├── test_payment.py
│   ├── test_blockchain.py
│   ├── test_blockchain_api.py
│   ├── test_integration.py
│   └── ...
├── requirements.txt            # Dépendances
└── GUIDE_UTILISATION.md       # Ce fichier
```

### Architecture des Données

#### Base de Données MongoDB
```
agrismart_db (6 collections)
├── blockchain_transactions      # Étapes produits
├── blockchain_blocks            # Blocs minés
├── smart_contracts              # Contrats intelligents
├── payment_transactions         # Transactions Moov
├── users                        # Utilisateurs
└── products                     # Produits
```

---

## Fonctionnement des Modules

### 1. Module de Paiement (Moov Money)

#### Comment ça marche?

```
CLIENT ACHÈTE → PAIEMENT INITIÉ → OTP GÉNÉRÉ → SMS ENVOYÉ
                                       ↓
                            CLIENT REÇOIT OTP
                                       ↓
                         CLIENT ENTRE OTP EN CONFIRMATION
                                       ↓
                            PAIEMENT CONFIRMÉ
                                       ↓
                          BLOCKCHAIN ENREGISTRE
```

#### Endpoints Disponibles

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payment/initiate` | Initier un paiement |
| POST | `/api/payment/confirm` | Confirmer avec OTP |
| GET | `/api/payment/status/{id}` | Vérifier statut |
| GET | `/api/payment/history` | Historique paiements |
| GET | `/api/payment/summary` | Résumé par utilisateur |
| POST | `/api/payment/refund` | Rembourser |
| GET | `/api/payment/stats` | Statistiques |
| GET | `/api/payment/all-users` | Tous les utilisateurs |

#### Exemple d'utilisation (curl)

```bash
# 1. Initier un paiement
curl -X POST "http://localhost:8000/api/payment/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_phone": "+225701234567",
    "amount": 400000,
    "product_id": "tomato_001",
    "buyer_id": "buyer_market_001",
    "seller_id": "farmer_abidjan_001",
    "quantity": 200,
    "unit_price": 2000,
    "description": "200kg tomates bio"
  }'

# Réponse:
{
  "transaction_id": "AGRI-ABC123DEF456",
  "amount": 400000,
  "status": "pending",
  "otp_code": null,
  "buyer_phone": "+225701234567"
}

# 2. Confirmer avec OTP
curl -X POST "http://localhost:8000/api/payment/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "AGRI-ABC123DEF456",
    "otp_code": "123456"
  }'

# Réponse:
{
  "status": "success",
  "transaction_id": "AGRI-ABC123DEF456",
  "amount": 400000
}
```

### 2. Module Blockchain de Traçabilité

#### Comment ça marche?

```
CRÉER CONTRAT → ENREGISTRER ÉTAPES → CONSTRUIRE TIMELINE
                       ↓
              CHAQUE ÉTAPE MINÉE
                       ↓
                 BLOCS CHAÎNÉS
                       ↓
             HASH SHA-256 IMMUABLE
```

#### Les 10 Étapes Produit

```
1. PLANTED      - Semis en terre
2. GROWING      - En croissance
3. HARVESTED    - Récolte
4. QUALITY_CHECKED - Contrôle qualité
5. PROCESSED    - Transformation/Séchage
6. PACKAGED     - Emballage
7. SHIPPED      - Expédition
8. IN_TRANSIT   - En transit
9. DELIVERED    - Livraison
10. SOLD        - Vente finalisée
```

#### Endpoints Disponibles

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/blockchain/smart-contract/create` | Créer contrat |
| POST | `/api/blockchain/record-stage` | Enregistrer étape |
| GET | `/api/blockchain/product-trace/{id}` | Trace complète |
| GET | `/api/blockchain/verify-authenticity/{id}` | Vérifier authenticité |
| GET | `/api/blockchain/contract/{id}` | Statut contrat |
| GET | `/api/blockchain/stats` | Statistiques réseau |
| GET | `/api/blockchain/farmer-stats/{id}` | Statut fermier |

#### Exemple d'utilisation (curl)

```bash
# 1. Créer un smart contract
curl -X POST "http://localhost:8000/api/blockchain/smart-contract/create" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "cacao_001",
    "farmer_id": "farmer_yamoussoukro_001",
    "farmer_name": "Amandine Kouassi",
    "product_type": "Cacao Fermente",
    "quantity": 500,
    "unit": "kg",
    "expected_delivery_days": 15,
    "buyer_id": "buyer_chocolate_001",
    "price": 2500000
  }'

# Réponse:
{
  "status": "success",
  "contract": {
    "contract_id": "SC-cacao_001-1765921000",
    "product_id": "cacao_001",
    "product_type": "Cacao Fermente",
    "quantity": 500,
    "price": 2500000,
    "status": "active"
  }
}

# 2. Enregistrer une étape (récolte)
curl -X POST "http://localhost:8000/api/blockchain/record-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "cacao_001",
    "stage": "harvested",
    "actor": "farmer",
    "actor_id": "farmer_yamoussoukro_001",
    "location": "Yamoussoukro, Region du Comoe",
    "temperature": 23.5,
    "humidity": 68,
    "quality_score": 88,
    "notes": "Recolte selective, feves saines",
    "contract_id": "SC-cacao_001-1765921000"
  }'

# Réponse:
{
  "status": "success",
  "transaction_id": "TX-cacao_001-harvested-1765921100",
  "stage": "harvested",
  "transaction_hash": "a3f5b2c8d9e1f4g7h0i2j3k4l5m6n7o8"
}

# 3. Récupérer la trace complète
curl -X GET "http://localhost:8000/api/blockchain/product-trace/cacao_001"

# Réponse:
{
  "status": "success",
  "data": {
    "product_id": "cacao_001",
    "contracts": [...],
    "transactions": [...],
    "timeline": [
      {
        "stage": "harvested",
        "actor": "farmer",
        "location": "Yamoussoukro",
        "temperature": 23.5,
        "humidity": 68,
        "quality_score": 88,
        "timestamp": "2025-12-16T21:00:00"
      },
      ...
    ],
    "authenticity": {
      "is_authentic": true,
      "blockchain_blocks": 1
    }
  }
}

# 4. Vérifier l'authenticité
curl -X GET "http://localhost:8000/api/blockchain/verify-authenticity/cacao_001"

# Réponse:
{
  "status": "success",
  "data": {
    "product_id": "cacao_001",
    "is_authentic": true,
    "transaction_count": 5,
    "blockchain_blocks": 1,
    "stages": ["harvested", "quality_checked", "processed", "packaged", "shipped"]
  }
}

# 5. Vérifier le statut du contrat
curl -X GET "http://localhost:8000/api/blockchain/contract/SC-cacao_001-1765921000"

# Réponse:
{
  "status": "success",
  "data": {
    "contract_id": "SC-cacao_001-1765921000",
    "conditions_met": true,
    "completion_percentage": 50.0,
    "stages_completed": 5,
    "total_stages": 10,
    "penalties": 0
  }
}

# 6. Statistiques du fermier
curl -X GET "http://localhost:8000/api/blockchain/farmer-stats/farmer_yamoussoukro_001"

# Réponse:
{
  "status": "success",
  "data": {
    "farmer_id": "farmer_yamoussoukro_001",
    "active_contracts": 3,
    "total_products": 1500,
    "reputation_score": 95.0,
    "total_penalties": 50
  }
}
```

### 3. Module SMS (Simulation)

#### Comment ça marche?

```
OTP GÉNÉRÉ (6 CHIFFRES) → SMS ENVOYÉ → LOG SAUVEGARDÉ
                              ↓
                      MODE SIMULATION:
                   Logs dans sms_demo_logs.json
                              ↓
                      MODE PRODUCTION:
                   Envoyé via Africa's Talking
```

#### Code d'utilisation

```python
from app.utils.sms import send_sms_async, get_sms_demo_data

# Envoyer un SMS
otp = "123456"
message = f"Votre code OTP AgriSmart: {otp}"
await send_sms_async("+225701234567", message)

# Récupérer l'historique SMS (démo)
history = get_sms_demo_data()
print(history)

# Résultat:
[
  {
    "timestamp": "2025-12-16T21:45:30.123456",
    "phone": "+225701234567",
    "message": "Votre code OTP AgriSmart: 123456",
    "status": "simulated",
    "mode": "simulation"
  },
  ...
]
```

---

## Exemples d'Utilisation

### Scénario Complet: Achat de Tomates

#### Phase 1: Créer le Contrat

```bash
curl -X POST "http://localhost:8000/api/blockchain/smart-contract/create" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "tomate_batch_001",
    "farmer_id": "farmer_abidjan_001",
    "farmer_name": "Paul Kouassi",
    "product_type": "Tomates Bio",
    "quantity": 200,
    "unit": "kg",
    "expected_delivery_days": 7,
    "buyer_id": "buyer_market_001",
    "price": 400000
  }'
```

#### Phase 2: Initier le Paiement

```bash
curl -X POST "http://localhost:8000/api/payment/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_phone": "+225701234567",
    "amount": 400000,
    "product_id": "tomate_batch_001",
    "buyer_id": "buyer_market_001",
    "seller_id": "farmer_abidjan_001",
    "quantity": 200,
    "unit_price": 2000,
    "description": "200kg tomates bio"
  }'
```

**OTP envoyé via SMS (simulation)**

#### Phase 3: Confirmer le Paiement

```bash
curl -X POST "http://localhost:8000/api/payment/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "AGRI-ABC123DEF456",
    "otp_code": "123456"
  }'
```

#### Phase 4: Enregistrer la Récolte

```bash
curl -X POST "http://localhost:8000/api/blockchain/record-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "tomate_batch_001",
    "stage": "harvested",
    "actor": "farmer",
    "actor_id": "farmer_abidjan_001",
    "location": "Ferme Kouassi, Abidjan",
    "temperature": 25.0,
    "humidity": 72,
    "quality_score": 92,
    "notes": "Recolte selectionnee, tomates rouges et fermes",
    "contract_id": "SC-tomate_batch_001-1765921000"
  }'
```

#### Phase 5: Enregistrer l'Expédition

```bash
curl -X POST "http://localhost:8000/api/blockchain/record-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "tomate_batch_001",
    "stage": "shipped",
    "actor": "transporter",
    "actor_id": "transporter_001",
    "location": "Port d'\''Abidjan",
    "temperature": 20.0,
    "humidity": 60,
    "notes": "Camion refroidi, depart a 6h00",
    "contract_id": "SC-tomate_batch_001-1765921000"
  }'
```

#### Phase 6: Enregistrer la Livraison

```bash
curl -X POST "http://localhost:8000/api/blockchain/record-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "tomate_batch_001",
    "stage": "delivered",
    "actor": "buyer",
    "actor_id": "buyer_market_001",
    "location": "Marche Central Cocody",
    "temperature": 22.0,
    "humidity": 65,
    "quality_score": 90,
    "notes": "Livraison confirmee, qualite maintenue",
    "contract_id": "SC-tomate_batch_001-1765921000"
  }'
```

#### Phase 7: Vérifier la Trace

```bash
curl -X GET "http://localhost:8000/api/blockchain/product-trace/tomate_batch_001"
```

**Résultat: Timeline complète avec tous les acteurs et conditions**

---

## Tests et Validation

### Tests Automatisés

#### 1. Test du Système de Paiement

```bash
cd c:\Users\Admin\OneDrive - ENSEA\Documents\Ingrid\Moov\AgriSmart
python scripts/test_payment.py
```

**Résultat attendu:**
```
✅ TEST 1: Initiation paiement
✅ TEST 2: Confirmation OTP
✅ TEST 3: Statut paiement
...
✅ TOUS LES 10 TESTS RÉUSSIS
```

#### 2. Test de la Blockchain

```bash
python scripts/test_blockchain.py
```

**Résultat attendu:**
```
✅ TEST 1: Création smart contract
✅ TEST 2: Enregistrement récolte
✅ TEST 3: Vérification authenticité
...
✅ TOUS LES 15 TESTS RÉUSSIS
```

#### 3. Test des Endpoints API

```bash
python scripts/test_blockchain_api.py
```

**Résultat attendu:**
```
✅ TEST 1: Créer smart contract
✅ TEST 2: Enregistrer étape
✅ TEST 3: Récupérer trace
✅ TEST 4: Vérifier authenticité
✅ TEST 5: Statut contrat
✅ TEST 6: Statistiques globales
✅ TEST 7: Statistiques fermier
```

#### 4. Test d'Intégration Complète

```bash
python scripts/test_integration.py
```

**Résultat attendu:**
```
PHASE 1: Créer smart contract [OK]
PHASE 2: Initier paiement [OK]
PHASE 3: Confirmer paiement [OK]
PHASE 4: Enregistrer récolte [OK]
...
PHASE 10: Vérifier statistiques fermier [OK]

CONCLUSION: ✅ TOUS LES TESTS RÉUSSIS
```

### Tests Manuels via Swagger UI

1. Accédez à: **http://localhost:8000/docs**
2. Cliquez sur un endpoint
3. Cliquez sur "Try it out"
4. Remplissez les paramètres
5. Cliquez sur "Execute"

---

## Dépannage

### Problème 1: Port 8000 Déjà en Utilisation

**Symptôme:**
```
ERROR:    [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Solution:**
```bash
# Trouver le processus
netstat -ano | Select-String "8000"

# Tuer le processus (remplacer PID)
taskkill /PID 12345 /F

# Relancer
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Problème 2: MongoDB Non Connectée

**Symptôme:**
```
pymongo.errors.ServerSelectionTimeoutError: No suitable servers found
```

**Solution:**
1. Vérifier la chaîne MONGODB_URL dans .env
2. Vérifier que MongoDB Atlas est accessible
3. Vérifier que l'IP est whitelistée dans MongoDB Atlas
4. Relancer le serveur

### Problème 3: SMS Non Envoyés

**Symptôme:**
```
Mode simulation: Aucune clé API valide
```

**Explication:**
- En mode simulation (par défaut), les SMS sont enregistrés localement
- Les logs sont disponibles dans `sms_demo_logs.json`
- En production, ajouter une clé API Africa's Talking valide dans .env

### Problème 4: Erreur 422 sur un Endpoint

**Symptôme:**
```
{"detail":[{"type":"missing","loc":["body"],"msg":"Field required"}]}
```

**Solution:**
- Vérifier les paramètres envoyés
- Consulter Swagger UI pour voir les champs requis
- Envoyer les données en JSON avec les bonnes clés

---

## Déploiement

### Déploiement Local (Développement)

```bash
# Mode avec rechargement automatique
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Déploiement Production (Windows)

```bash
# Créer un service Windows
nssm install AgriSmartAPI python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
nssm start AgriSmartAPI
```

### Déploiement sur Cloud (Heroku/Railway)

#### 1. Créer Procfile
```
web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

#### 2. Créer requirements-prod.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
motor==3.3.2
pymongo==4.6.0
pydantic==2.5.0
python-dotenv==1.0.0
africastalking==1.3.1
```

#### 3. Déployer
```bash
git push heroku main
```

### Déploiement Docker

#### 1. Créer Dockerfile
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Construire et lancer
```bash
docker build -t agrismart:latest .
docker run -p 8000:8000 --env-file .env agrismart:latest
```

---

## Checklist de Démarrage

- [ ] Python 3.13+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier .env créé avec les bonnes valeurs
- [ ] MongoDB accessible
- [ ] Serveur lancé: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] Swagger UI accessible: http://localhost:8000/docs
- [ ] Tests lancés et réussis: `python scripts/test_integration.py`

---

## Résumé

### Commandes Essentielles

```bash
# Lancer le serveur
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Tester les endpoints
curl http://localhost:8000/api/blockchain/stats

# Accéder à Swagger UI
# http://localhost:8000/docs

# Lancer les tests
python scripts/test_integration.py

# Voir les logs SMS (simulation)
cat sms_demo_logs.json
```

### Stats du Système

```
✅ 8 endpoints Paiement (Moov Money)
✅ 7 endpoints Blockchain (Traçabilité)
✅ 10 étapes produit suivies
✅ 2 systèmes intégrés (Paiement + Blockchain)
✅ 100% des tests réussis
✅ Prêt pour démonstration et production
```

---

**AgriSmart** - Système de Traçabilité Agricole Blockchain
*Documentation: 2025-12-16*
