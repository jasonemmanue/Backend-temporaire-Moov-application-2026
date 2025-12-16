# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- Base de données ---
    MONGODB_URL: str
    MONGODB_DATABASE: str
    
    # Redis (Optionnel, on met une valeur par défaut ou Optional)
    REDIS_URL: Optional[str] = None

    # --- Sécurité & JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # --- Africa's Talking (SMS) ---
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str
    AT_SENDER_ID: str = "AGRISMART_CI"

    # --- OTP ---
    OTP_EXPIRE_MINUTES: int = 5
    OTP_LENGTH: int = 6

    # --- Blockchain (Optionnel pour le démarrage si pas dans .env) ---
    POLYGON_RPC_URL: Optional[str] = None
    CONTRACT_ADDRESS: Optional[str] = None
    PRIVATE_KEY: Optional[str] = None
    CHAIN_ID: Optional[int] = 80002
    WEB3_STORAGE_TOKEN: Optional[str] = None
    
    # --- Moov Money (Paiements) ---
    MOOV_API_KEY: str = "test_api_key"  # Clé test par défaut (simulation)
    MOOV_MERCHANT_ID: str = "merchant_test"  # ID marchand test

    # Configuration Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=False,  # Permet MONGODB_URL ou mongodb_url
        extra="ignore"         # IMPORTANT: Ignore les variables du .env qui ne sont pas déclarées ici (évite le crash)
    )

settings = Settings()