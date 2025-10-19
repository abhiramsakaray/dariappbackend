#!/usr/bin/env python3
"""
Database initialization and seeding script
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import init_db, AsyncSessionLocal
from app.crud.token import seed_default_data
from app.core.security import create_initial_admin


async def init_database():
    """Initialize database with tables and default data"""
    print("Initializing database...")
    
    try:
        # Create tables
        await init_db()
        print("✓ Database tables created")
        
        # Seed default data
        async with AsyncSessionLocal() as db:
            await seed_default_data(db)
        print("✓ Default tokens and fiat currencies seeded")
        
        # Create initial admin
        await create_initial_admin()
        print("✓ Initial admin user created")
        
        print("\n🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())
