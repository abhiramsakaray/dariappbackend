from pydantic_settings import BaseSettings
from typing import List
import secrets
import os


def fix_postgres_url(url: str) -> str:
    """Convert postgres:// URLs to postgresql:// for SQLAlchemy compatibility"""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def fix_postgres_url_async(url: str) -> str:
    """Convert postgres:// URLs to postgresql+asyncpg:// for async SQLAlchemy"""
    print(f"🔧 Converting URL for async: {url[:50]}...")  # Debug log
    
    if url.startswith("postgres://"):
        result = url.replace("postgres://", "postgresql+asyncpg://", 1)
        print(f"✅ Converted postgres:// to postgresql+asyncpg://")
    elif url.startswith("postgresql://"):
        result = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        print(f"✅ Converted postgresql:// to postgresql+asyncpg://")
    elif url.startswith("postgresql+asyncpg://"):
        print(f"✅ URL already uses asyncpg driver")
        result = url
    else:
        print(f"⚠️ Unknown URL format, using as-is")
        result = url
    
    # For asyncpg, we need to convert sslmode to ssl parameter
    if "sslmode=require" in result:
        result = result.replace("sslmode=require", "ssl=require")
        print(f"🔧 Converted sslmode=require to ssl=require for asyncpg")
    elif "sslmode=disable" in result:
        result = result.replace("sslmode=disable", "ssl=disable")  
        print(f"🔧 Converted sslmode=disable to ssl=disable for asyncpg")
    elif "sslmode=prefer" in result:
        result = result.replace("sslmode=prefer", "ssl=prefer")
        print(f"🔧 Converted sslmode=prefer to ssl=prefer for asyncpg")
    
    return result


class Settings(BaseSettings):
    # Database - Support environment variables for production
    _base_db_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://dari_user:dari_password@localhost:5432/dari_wallet_v2")
    
    DATABASE_URL: str = fix_postgres_url_async(_base_db_url)
    DATABASE_URL_SYNC: str = fix_postgres_url(os.getenv("DATABASE_URL_SYNC") or fix_postgres_url(_base_db_url))
    
    # Redis - Support environment variable
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AES Encryption
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # CORS - Use string instead of List to avoid JSON parsing issues
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # OTP
    OTP_EXPIRE_MINUTES: int = 10
    OTP_EMAIL_ENABLED: bool = True
    OTP_SMS_ENABLED: bool = False
    
    # Email - SendGrid (Recommended for cloud deployment)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    USE_SENDGRID: bool = os.getenv("USE_SENDGRID", "true").lower() in ("1", "true", "yes")
    
    # Email - SMTP Fallback (for local development)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@dariwallet.com")
    # Transport flags
    # If port is 465 use implicit SSL (SMTP_SSL). If 587 use STARTTLS by default.
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "").lower() in ("1", "true", "yes")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "").lower() in ("1", "true", "yes")
    
    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # Firebase Cloud Messaging (FCM) for push notifications
    # Legacy API (deprecated but simpler)
    FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")
    
    # V1 API (recommended - requires service account)
    FCM_PROJECT_ID: str = os.getenv("FCM_PROJECT_ID", "")
    FCM_SERVICE_ACCOUNT_PATH: str = os.getenv("FCM_SERVICE_ACCOUNT_PATH", "")
    
    # Blockchain
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    POLYGON_TESTNET_RPC_URL: str = "https://polygon-mumbai.g.alchemy.com/v2/demo"
    POLYGON_CHAIN_ID: int = 137
    POLYGON_TESTNET_CHAIN_ID: int = 80002  # Polygon Amoy testnet
    USE_TESTNET: bool = True
    
    # Token Contracts (Mainnet)
    USDC_CONTRACT_ADDRESS: str = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    USDT_CONTRACT_ADDRESS: str = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
    
    # Token Contracts (Testnet)
    USDC_TESTNET_CONTRACT_ADDRESS: str = "0x9999f7Fea5938fD3b1E26A12c3f2fb024e194f97"
    USDT_TESTNET_CONTRACT_ADDRESS: str = "0xBD21A10F619BE90d6066c941b04e4B3B9b3d7ED1"
    
    # DARI Relayer Wallet (for gasless transactions)
    # This wallet pays gas fees on behalf of users
    RELAYER_PRIVATE_KEY: str = os.getenv("RELAYER_PRIVATE_KEY", "")
    RELAYER_ADDRESS: str = os.getenv("RELAYER_ADDRESS", "")
    ENABLE_GASLESS: bool = os.getenv("ENABLE_GASLESS", "true").lower() in ("1", "true", "yes")
    
    # Gas fee limits (safety measures)
    MAX_GAS_PRICE_GWEI: int = 500  # Don't pay more than 500 Gwei
    MIN_RELAYER_BALANCE_MATIC: float = 1.0  # Alert if relayer balance < 1 MATIC
    
    # CoinGecko
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    PRICE_UPDATE_INTERVAL_MINUTES: int = 5
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: str = ".pdf,.jpg,.jpeg,.png"
    UPLOAD_DIRECTORY: str = "./uploads"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Admin
    ADMIN_EMAIL: str = "admin@dariwallet.com"
    ADMIN_PASSWORD: str = "admin123"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_file_extensions_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [ext.strip() for ext in self.ALLOWED_FILE_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
