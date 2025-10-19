from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force PostgreSQL dialect registration
try:
    import psycopg2
    import sqlalchemy.dialects.postgresql
except ImportError:
    pass

from app.core.config import settings

# Global variables for lazy initialization
_async_engine = None
_sync_engine = None
_async_session_local = None
_sync_session_local = None

def get_async_engine():
    """Get or create async engine with timeout protection"""
    global _async_engine
    if _async_engine is None:
        # Ensure we use the properly converted async URL
        from app.core.config import fix_postgres_url_async
        async_url = fix_postgres_url_async(settings.DATABASE_URL)
        print(f"🔍 Creating async engine with URL: {async_url}")
        _async_engine = create_async_engine(
            async_url,
            echo=True if settings.ENVIRONMENT == "development" else False,
            pool_size=5,  # Reduced pool size to prevent hanging
            max_overflow=10,  # Reduced overflow
            pool_timeout=30,  # Increased to 30 seconds for blockchain operations
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Verify connections before use
            # Add query timeout settings - more reasonable for production
            connect_args={
                "command_timeout": 30,  # 30 second command timeout (for blockchain ops)
                "server_settings": {
                    "statement_timeout": "30s",  # 30 second statement timeout
                    "lock_timeout": "10s",  # 10 second lock timeout
                    "idle_in_transaction_session_timeout": "60s"  # 60 second idle timeout for blockchain
                }
            }
        )
    return _async_engine

def get_sync_engine():
    """Get or create sync engine with timeout protection"""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.DATABASE_URL_SYNC,
            echo=True if settings.ENVIRONMENT == "development" else False,
            pool_size=5,  # Reduced pool size to prevent hanging
            max_overflow=10,  # Reduced overflow
            pool_timeout=5,  # Reduced timeout to 5 seconds
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Verify connections before use
            # Add query timeout settings
            connect_args={
                "options": "-c statement_timeout=5s -c lock_timeout=3s"
            }
        )
    return _sync_engine

def get_async_session_local():
    """Get or create async session local"""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local

def get_sync_session_local():
    """Get or create sync session local"""
    global _sync_session_local
    if _sync_session_local is None:
        _sync_session_local = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _sync_session_local

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session with improved error handling"""
    session_local = get_async_session_local()
    async with session_local() as session:
        try:
            yield session
        except Exception as e:
            # Rollback on any exception
            await session.rollback()
            raise
        finally:
            # Close session safely, handling stale connections
            try:
                await session.close()
            except Exception as close_error:
                # Log but don't raise if close fails (connection already dead)
                print(f"Warning: Error closing session: {close_error}")
                pass


def get_sync_db():
    """Get sync database session for Celery tasks"""
    session_local = get_sync_session_local()
    db = session_local()
    try:
        yield db
    finally:
        db.close()


async def dispose_engine_pool():
    """Dispose of the engine connection pool to clear stale connections"""
    global _async_engine, _sync_engine
    try:
        if _async_engine is not None:
            await _async_engine.dispose()
            print("✅ Disposed async engine connection pool")
        if _sync_engine is not None:
            _sync_engine.dispose()
            print("✅ Disposed sync engine connection pool")
    except Exception as e:
        print(f"⚠️  Warning: Error disposing engine pools: {e}")


async def init_db():
    """Initialize database tables and seed initial data"""
    # First, clear any stale connections from previous sessions
    await dispose_engine_pool()
    
    # Import all models to ensure they are registered with SQLAlchemy
    from app.models.user import User
    from app.models.kyc import KYCRequest
    from app.models.wallet import Wallet
    from app.models.token import Token, TokenBalance, FiatCurrency
    from app.models.transaction import Transaction as TransactionModel
    from app.models.address_resolver import AddressResolver
    from app.core.config import settings
    
    # Create tables
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed initial tokens
    await seed_tokens()


async def seed_tokens():
    """Seed initial tokens in the database"""
    from app.models.token import Token
    from app.core.config import settings
    
    async with get_async_session_local()() as db:
        # Check if tokens already exist
        from sqlalchemy import select
        result = await db.execute(select(Token))
        if result.scalars().first():
            return  # Tokens already seeded
        
        # Define tokens based on environment
        if settings.USE_TESTNET:
            tokens = [
                {
                    "name": "USD Coin",
                    "symbol": "USDC",
                    "contract_address": settings.USDC_TESTNET_CONTRACT_ADDRESS,
                    "decimals": 6,
                    "coingecko_id": "usd-coin"
                },
                {
                    "name": "Polygon",
                    "symbol": "MATIC",
                    "contract_address": "0x0000000000000000000000000000000000000000",  # Native token
                    "decimals": 18,
                    "coingecko_id": "matic-network"
                }
            ]
        else:
            tokens = [
                {
                    "name": "USD Coin",
                    "symbol": "USDC",
                    "contract_address": settings.USDC_CONTRACT_ADDRESS,
                    "decimals": 6,
                    "coingecko_id": "usd-coin"
                },
                {
                    "name": "Polygon",
                    "symbol": "MATIC",
                    "contract_address": "0x0000000000000000000000000000000000000000",  # Native token
                    "decimals": 18,
                    "coingecko_id": "matic-network"
                }
            ]
        
        # Create tokens
        for token_data in tokens:
            token = Token(**token_data)
            db.add(token)
        
        await db.commit()
        print("✅ Initial tokens seeded successfully")
