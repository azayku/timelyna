"""
Big dataset seed — 500 employees, 2 admins, 4 payroll, 300 clients, 1000 projects,
timesheet entries + approvals for the last 12 weeks.

Run: python backend/seed_big.py
"""
from __future__ import annotations

import asyncio
import random
import sys
import os
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import bcrypt
from faker import Faker
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.employee import Employee
from app.models.auth import RefreshToken, LoginAttempt, PasswordResetToken
from app.models.client import Client
from app.models.project import Project
from app.models.timesheet_entry import TimesheetEntry
from app.models.approval import Approval
from app.models.export import Export
from app.models.invoice import Invoice
from app.models.organization_license import OrganizationLicense
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference

# PostgreSQL connection for Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://timelyna:changeme@localhost:5432/timelyna"
)

fake = Faker("fr_FR")
Faker.seed(42)
random.seed(42)

TASK_TYPES = ["dev", "design", "testing", "meeting", "doc", "other"]
DEPARTMENTS = ["Engineering", "Design", "QA", "Product", "DevOps", "Data", "Support", "Finance"]


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=6)).decode()


def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Don't create tables - use Alembic migrations instead
    print("✓ Using existing database schema")

    async with factory() as db:
        # ── Check if already seeded ────────────────────────────────────────
        result = await db.execute(select(Employee))
        existing = result.scalars().all()
        if len(existing) > 10:
            print(f"Already seeded ({len(existing)} employees). Delete the DB to re-seed.")
            return

        print("Seeding... (this may take ~30s)")

        # ══════════════════════════════════════════════════════════════════
        # 1. ADMINS (2)
        # ══════════════════════════════════════════════════════════════════
        admins = []
        for i in range(2):
            a = Employee(
                email=f"admin{i+1}@timelyna.com",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password_hash=hash_pw("Admin1234!"),
                role="admin",
                employment_status="active",
                department="Management",
                org_id=1,
            )
            db.add(a)
            admins.append(a)
        await db.flush()
        print(f"  ✓ {len(admins)} admins")

        # ══════════════════════════════════════════════════════════════════
        # 2. PAYROLL (4)
        # ══════════════════════════════════════════════════════════════════
        payrolls = []
        for i in range(4):
            p = Employee(
                email=f"payroll{i+1}@timelyna.com",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password_hash=hash_pw("Payroll1234!"),
                role="payroll",
                employment_status="active",
                department="Finance",
                org_id=1,
            )
            db.add(p)
            payrolls.append(p)
        await db.flush()
        print(f"  ✓ {len(payrolls)} payroll managers")

        # ══════════════════════════════════════════════════════════════════
        # 3. MANAGERS (20)
        # ══════════════════════════════════════════════════════════════════
        managers = []
        for i in range(20):
            m = Employee(
                email=fake.unique.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password_hash=hash_pw("Manager1234!"),
                role="manager",
                employment_status="active",
                department=random.choice(DEPARTMENTS),
                hourly_cost=Decimal(str(round(random.uniform(40, 80), 2))),
                org_id=1,
            )
            db.add(m)
            managers.append(m)
        await db.flush()
        print(f"  ✓ {len(managers)} managers")

        # ══════════════════════════════════════════════════════════════════
        # 4. EMPLOYEES (500)
        # ══════════════════════════════════════════════════════════════════
        employees = []
        for i in range(500):
            mgr = random.choice(managers)
            e = Employee(
                email=fake.unique.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password_hash=hash_pw("Employee1234!"),
                role="employee",
                employment_status=random.choices(["active", "inactive"], weights=[95, 5])[0],
                department=random.choice(DEPARTMENTS),
                manager_id=mgr.employee_id,
                hourly_cost=Decimal(str(round(random.uniform(25, 60), 2))),
                hire_date=fake.date_between(start_date="-5y", end_date="today"),
                org_id=1,
            )
            db.add(e)
            employees.append(e)
            if i % 100 == 99:
                await db.flush()
                print(f"    {i+1}/500 employees...")
        await db.flush()
        print(f"  ✓ {len(employees)} employees")

        # ══════════════════════════════════════════════════════════════════
        # 5. CLIENTS (300)
        # ══════════════════════════════════════════════════════════════════
        clients = []
        for i in range(300):
            c = Client(
                client_name=fake.company(),
                company_name=fake.company(),
                email=fake.unique.company_email(),
                phone=fake.phone_number()[:20],
                address=fake.address()[:200],
                default_billing_rate=Decimal(str(round(random.uniform(80, 250), 2))),
                currency=random.choices(["EUR", "USD", "GBP"], weights=[70, 20, 10])[0],
                client_status=random.choices(["active", "inactive"], weights=[90, 10])[0],
            )
            db.add(c)
            clients.append(c)
            if i % 100 == 99:
                await db.flush()
                print(f"    {i+1}/300 clients...")
        await db.flush()
        active_clients = [c for c in clients if c.client_status == "active"]
        print(f"  ✓ {len(clients)} clients ({len(active_clients)} active)")

        # ══════════════════════════════════════════════════════════════════
        # 6. PROJECTS (1000) — distributed across clients
        # ══════════════════════════════════════════════════════════════════
        projects = []
        used_codes: set[str] = set()
        all_employee_ids = [e.employee_id for e in employees]

        for i in range(1000):
            client = random.choice(active_clients)
            mgr = random.choice(managers)

            # Unique project code
            while True:
                code = f"{fake.lexify('???').upper()}-{random.randint(1000, 9999)}"
                if code not in used_codes:
                    used_codes.add(code)
                    break

            # Assign 3–15 random employees as team members
            team_size = random.randint(3, 15)
            team = random.sample(all_employee_ids, min(team_size, len(all_employee_ids)))
            if mgr.employee_id not in team:
                team.append(mgr.employee_id)

            start = fake.date_between(start_date="-2y", end_date="-1m")
            status = random.choices(
                ["active", "active", "active", "paused", "completed"],
                weights=[50, 20, 15, 10, 5]
            )[0]

            p = Project(
                client_id=client.client_id,
                project_name=f"{fake.bs().title()} {fake.word().title()}",
                project_code=code,
                description=fake.sentence(nb_words=10),
                status=status,
                billing_rate=Decimal(str(round(random.uniform(80, 300), 2))),
                manager_id=mgr.employee_id,
                team_members=team,
                start_date=start,
                budget_hours=Decimal(str(round(random.uniform(50, 2000), 0))),
                budget_amount=Decimal(str(round(random.uniform(5000, 500000), 2))),
            )
            db.add(p)
            projects.append(p)
            if i % 200 == 199:
                await db.flush()
                print(f"    {i+1}/1000 projects...")
        await db.flush()
        active_projects = [p for p in projects if p.status == "active"]
        print(f"  ✓ {len(projects)} projects ({len(active_projects)} active)")

        # ══════════════════════════════════════════════════════════════════
        # 7. TIMESHEET ENTRIES — last 12 weeks for active employees
        # ══════════════════════════════════════════════════════════════════
        today = date.today()
        # Build employee → projects map
        emp_projects: dict[int, list[Project]] = {}
        for proj in active_projects:
            if proj.team_members:
                for eid in proj.team_members:
                    emp_projects.setdefault(eid, []).append(proj)

        active_employees = [e for e in employees if e.employment_status == "active"]
        # Only seed entries for a sample of employees to keep it fast
        sample_employees = random.sample(active_employees, min(100, len(active_employees)))

        entry_count = 0
        approval_count = 0

        for emp in sample_employees:
            emp_projs = emp_projects.get(emp.employee_id, [])
            if not emp_projs:
                continue

            for week_offset in range(12):
                week_monday = monday_of_week(today) - timedelta(weeks=week_offset + 1)
                # Skip ~20% of weeks (employee was absent/on leave)
                if random.random() < 0.2:
                    continue

                # Work 3–5 days per week
                work_days = random.sample(range(5), random.randint(3, 5))
                week_entries = []

                for day_offset in work_days:
                    work_date = week_monday + timedelta(days=day_offset)
                    if work_date > today:
                        continue

                    proj = random.choice(emp_projs)
                    hours = Decimal(str(round(random.choice([4, 6, 7, 7.5, 8, 8.5]), 2)))

                    entry = TimesheetEntry(
                        employee_id=emp.employee_id,
                        project_id=proj.project_id,
                        work_date=work_date,
                        hours_worked=hours,
                        description=fake.sentence(nb_words=6),
                        task_type=random.choice(TASK_TYPES),
                        billable_flag=random.random() > 0.1,
                        status="draft",
                    )
                    db.add(entry)
                    week_entries.append(entry)

                if not week_entries:
                    continue

                await db.flush()

                # Determine approval status for this week
                # Recent weeks (0-1): draft or submitted
                # Older weeks (2-11): submitted, approved, or rejected
                if week_offset == 0:
                    # Current week — keep as draft
                    pass
                elif week_offset == 1:
                    # Last week — submitted
                    for e in week_entries:
                        e.status = "submitted"
                        e.submitted_at = week_monday + timedelta(days=5)
                    approval = Approval(
                        employee_id=emp.employee_id,
                        manager_id=emp.manager_id,
                        week_start=week_monday,
                        status="pending",
                    )
                    db.add(approval)
                    approval_count += 1
                else:
                    # Older weeks — approved or rejected
                    outcome = random.choices(
                        ["approved", "rejected"],
                        weights=[85, 15]
                    )[0]
                    for e in week_entries:
                        e.status = outcome
                        e.submitted_at = week_monday + timedelta(days=5)
                        if outcome == "approved":
                            e.approved_at = week_monday + timedelta(days=6)
                    approval = Approval(
                        employee_id=emp.employee_id,
                        manager_id=emp.manager_id,
                        week_start=week_monday,
                        status=outcome,
                        decided_at=week_monday + timedelta(days=6),
                        rejection_reason="Heures incorrectes, veuillez corriger." if outcome == "rejected" else None,
                    )
                    db.add(approval)
                    approval_count += 1

                entry_count += len(week_entries)

            if entry_count % 500 == 0 and entry_count > 0:
                await db.flush()

        await db.flush()
        print(f"  ✓ {entry_count} timesheet entries")
        print(f"  ✓ {approval_count} approvals")

        await db.commit()

    print()
    print("═" * 50)
    print("✓ Seed terminé !")
    print()
    print("Comptes de connexion :")
    print()
    print("  ADMIN")
    print("    admin1@timelyna.com / Admin1234!")
    print("    admin2@timelyna.com / Admin1234!")
    print()
    print("  PAYROLL (gestionnaire de paie)")
    print("    payroll1@timelyna.com / Payroll1234!")
    print("    payroll2@timelyna.com / Payroll1234!")
    print("    payroll3@timelyna.com / Payroll1234!")
    print("    payroll4@timelyna.com / Payroll1234!")
    print()
    print("  EMPLOYEE (500 comptes)")
    print("    Mot de passe : Employee1234!")
    print()
    print("  MANAGER (20 comptes)")
    print("    Mot de passe : Manager1234!")
    print("═" * 50)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
