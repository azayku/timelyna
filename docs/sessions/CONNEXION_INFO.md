# Informations de Connexion - TimesheetPro

## Compte Admin par défaut

**Email**: `admin@timesheetpro.com`
**Mot de passe**: Le mot de passe a été défini lors de la première création du container

## Problème actuel

Le compte admin existe déjà dans la base de données mais le mot de passe n'est pas connu.

## Solutions

### Solution 1: Réinitialiser le mot de passe admin (RECOMMANDÉ)

Exécutez ce script pour réinitialiser le mot de passe admin:

```bash
docker exec -it timesheetpro-backend python - <<'EOF'
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select
import bcrypt
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timesheetpro:changeme@postgres:5432/timesheetpro")

async def reset_admin_password():
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db:
        from app.models.employee import Employee
        
        # Find admin
        result = await db.execute(select(Employee).where(Employee.email == "admin@timesheetpro.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Admin account not found!")
            return
        
        # Reset password to 'admin123'
        new_password = "admin123"
        pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=10)).decode()
        admin.password_hash = pw_hash
        
        await db.commit()
        print(f"✅ Admin password reset successfully!")
        print(f"Email: admin@timesheetpro.com")
        print(f"Password: {new_password}")
    
    await engine.dispose()

asyncio.run(reset_admin_password())
EOF
```

### Solution 2: Supprimer et recréer le compte admin

```bash
# 1. Supprimer le compte admin existant
docker exec -it timesheetpro-backend python - <<'EOF'
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, delete
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timesheetpro:changeme@postgres:5432/timesheetpro")

async def delete_admin():
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db:
        from app.models.employee import Employee
        
        await db.execute(delete(Employee).where(Employee.email == "admin@timesheetpro.com"))
        await db.commit()
        print("✅ Admin account deleted")
    
    await engine.dispose()

asyncio.run(delete_admin())
EOF

# 2. Redémarrer le backend pour recréer le compte
docker-compose restart backend
```

### Solution 3: Créer un nouveau compte admin

```bash
docker exec -it timesheetpro-backend python - <<'EOF'
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import bcrypt
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://timesheetpro:changeme@postgres:5432/timesheetpro")

async def create_new_admin():
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db:
        from app.models.employee import Employee
        
        email = "admin2@timesheetpro.com"
        password = "admin123"
        
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()
        admin = Employee(
            email=email,
            first_name="Admin",
            last_name="Secondary",
            username="admin2",
            password_hash=pw_hash,
            role="admin",
            employment_status="active",
            org_id=1,
        )
        db.add(admin)
        await db.commit()
        print(f"✅ New admin account created!")
        print(f"Email: {email}")
        print(f"Password: {password}")
    
    await engine.dispose()

asyncio.run(create_new_admin())
EOF
```

## Après réinitialisation

Une fois le mot de passe réinitialisé, vous pourrez vous connecter avec:

- **Email**: `admin@timesheetpro.com`
- **Mot de passe**: `admin123`

## URL de l'application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:5050

## Autres comptes (après seed)

Après avoir exécuté le script de seed, vous aurez accès à:

- **Admins**: `[nome].[cognome]@admin.test.it` / `password123`
- **Managers**: `[nome].[cognome]@manager.test.it` / `password123`
- **Finance**: `[nome].[cognome]@finance.test.it` / `password123`
- **Employés**: `[nome].[cognome]@emp[N].test.it` / `password123`

Exemples:
- `mario.rossi@admin.test.it` / `password123`
- `giulia.bianchi@manager.test.it` / `password123`
