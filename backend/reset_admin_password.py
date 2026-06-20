"""
Script pour réinitialiser le mot de passe admin.
Usage: python reset_admin_password.py
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select
import bcrypt
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timelyna:changeme@postgres:5432/timelyna")

async def reset_admin_password():
    """Réinitialise le mot de passe du compte admin à 'admin123'."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with factory() as db:
        from app.models.employee import Employee
        
        # Trouver le compte admin
        result = await db.execute(
            select(Employee).where(Employee.email == "admin@timelyna.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ Compte admin introuvable!")
            print("Email recherché: admin@timelyna.com")
            return
        
        # Réinitialiser le mot de passe
        new_password = "admin123"
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=10)).decode()
        admin.password_hash = pw_hash
        
        await db.commit()
        
        print("=" * 60)
        print("✅ MOT DE PASSE ADMIN RÉINITIALISÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"Email:    admin@timelyna.com")
        print(f"Password: {new_password}")
        print("=" * 60)
        print("\nVous pouvez maintenant vous connecter sur http://localhost")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
