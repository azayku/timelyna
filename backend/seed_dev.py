"""
Dev seed script — creates demo accounts for development.
Run: docker compose exec backend python seed_dev.py
"""
import asyncio
import sys
import os

# Make sure we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import bcrypt
from sqlalchemy import select

# Import database session
from app.core.database import _get_engine, _get_session_factory

# Import all models
from app.models.employee import Employee
from app.models.client import Client
from app.models.project import Project
from app.models.module_license import ModuleLicense


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def seed():
    """Seed the database with demo data."""
    engine = _get_engine()
    session_factory = _get_session_factory()

    async with session_factory() as db:
        # Check if already seeded
        existing = await db.execute(select(Employee).where(Employee.email == "admin@timesheetpro.com"))
        if existing.scalar_one_or_none():
            print("✓ Already seeded — skipping")
            return

        print("🌱 Seeding database...")

        # ── Admin ──────────────────────────────────────────────────────────
        admin = Employee(
            email="admin@timesheetpro.com",
            first_name="Alice",
            last_name="Admin",
            password_hash=hash_pw("Admin1234!"),
            role="admin",
            employment_status="active",
            org_id=1,
        )
        db.add(admin)
        await db.flush()

        # ── Manager ────────────────────────────────────────────────────────
        manager = Employee(
            email="manager@timesheetpro.com",
            first_name="Marc",
            last_name="Manager",
            password_hash=hash_pw("Manager1234!"),
            role="manager",
            employment_status="active",
            org_id=1,
        )
        
        db.add(manager)
        await db.flush()

        # ── Employee ───────────────────────────────────────────────────────
        emp = Employee(
            email="employee@timesheetpro.com",
            first_name="Emma",
            last_name="Employee",
            password_hash=hash_pw("Employee1234!"),
            role="employee",
            employment_status="active",
            manager_id=manager.employee_id,
            org_id=1,
        )
        db.add(emp)
        await db.flush()

        # ── Finance ────────────────────────────────────────────────────────
        finance = Employee(
            email="finance@timesheetpro.com",
            first_name="Frank",
            last_name="Finance",
            password_hash=hash_pw("Finance1234!"),
            role="finance",
            employment_status="active",
            org_id=1,
        )
        db.add(finance)
        await db.flush()

        # ── Client ─────────────────────────────────────────────────────────
        from datetime import date
        
        client = Client(
            client_name="Acme Corp",
            company_name="Acme Corporation",
            email="billing@acme.com",
            default_billing_rate=150.00,
            currency="EUR",
            client_status="active",
        )
        db.add(client)
        await db.flush()

        # ── Project ────────────────────────────────────────────────────────
        project = Project(
            client_id=client.client_id,
            project_name="Website Redesign",
            project_code="ACME-WEB-001",
            description="Full website redesign for Acme Corp",
            status="active",
            billing_rate=150.00,
            manager_id=manager.employee_id,
            team_members=[manager.employee_id, emp.employee_id],
            start_date=date(2025, 1, 1),
            budget_hours=200.00,
        )
        db.add(project)
        await db.flush()

        project2 = Project(
            client_id=client.client_id,
            project_name="Mobile App",
            project_code="ACME-MOB-001",
            description="Mobile application development",
            status="active",
            billing_rate=175.00,
            manager_id=manager.employee_id,
            team_members=[manager.employee_id, emp.employee_id],
            start_date=date(2025, 2, 1),
            budget_hours=100.00,
        )
        db.add(project2)
        await db.flush()

        # ── Finance Pro License (Inactive for demo) ─────────────────────────
        # Create an inactive license to demo the license gate
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        license = ModuleLicense(
            org_id=1,
            module_name="finance_pro",
            license_key="DEMO-INACTIVE-LICENSE-2025",  # Demo key
            expires_at=yesterday,  # Expired yesterday
        )
        db.add(license)
        await db.flush()

        await db.commit()

    print("✅ Demo accounts created:")
    print()
    print("  👤 ADMIN")
    print("    Email   : admin@timesheetpro.com")
    print("    Password: Admin1234!")
    print()
    print("  👤 MANAGER")
    print("    Email   : manager@timesheetpro.com")
    print("    Password: Manager1234!")
    print()
    print("  👤 EMPLOYEE")
    print("    Email   : employee@timesheetpro.com")
    print("    Password: Employee1234!")
    print()
    print("  👤 FINANCE")
    print("    Email   : finance@timesheetpro.com")
    print("    Password: Finance1234!")
    print()
    print("  📁 Projects: 'Website Redesign' + 'Mobile App' (client: Acme Corp)")
    print()
    print("✅ Seeding complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
