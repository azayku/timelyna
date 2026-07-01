"""Reset the database and seed a large Timelyna construction demo dataset.

This script truncates the application tables, then creates:
- 10 organizations
- 20 clients, 10 projects per client
- 100 employees total, including 20 managers, 5 finance, 5 payroll/RH, and 3 admins
- project teams, skills, pointages, approvals, and absences
- a mix of ongoing projects, future not-started projects, completed projects, and employees without missions

Run inside the backend container:
    python seed_reset_massive_demo.py
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
from faker import Faker
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import _get_session_factory
from app.models import (  # noqa: F401 - imported to register metadata
    Absence,
    Approval,
    Base,
    Client,
    Employee,
    EmployeeSkill,
    OrgSettings,
    Organization,
    Project,
    ProjectRequiredSkill,
    ProjectTeamMember,
    SkillRate,
    TimesheetEntry,
)


fake = Faker("it_IT")
Faker.seed(2026)
random.seed(2026)

TODAY = date(2026, 6, 20)
ADMIN_PASSWORD = "Admin2026!"
MANAGER_PASSWORD = "Manager2026!"
FINANCE_PASSWORD = "Finance2026!"
PAYROLL_PASSWORD = "Payroll2026!"
EMPLOYEE_PASSWORD = "Employee2026!"

ROLE_PASSWORDS = {
    "admin": ADMIN_PASSWORD,
    "manager": MANAGER_PASSWORD,
    "finance": FINANCE_PASSWORD,
    "payroll": PAYROLL_PASSWORD,
    "employee": EMPLOYEE_PASSWORD,
}

ORG_NAMES = [
    "Alfa Costruzioni Milano S.r.l.",
    "Beta Impianti Roma S.r.l.",
    "Gamma Idraulica Torino S.r.l.",
    "Delta Ristrutturazioni Napoli S.r.l.",
    "Epsilon Edilizia Bologna S.r.l.",
    "Zeta Energia Verona S.r.l.",
    "Eta Cantieri Firenze S.r.l.",
    "Theta Servizi Genova S.r.l.",
    "Iota Tecno Lavori Padova S.r.l.",
    "Kappa Opere Pubbliche Bari S.r.l.",
]

CLIENTS = [
    ("Rossi Costruzioni", "Rossi Costruzioni S.r.l.", "Milano", "Via Roma 12, 20121 Milano MI, Italia"),
    ("Bianchi Impianti", "Bianchi Impianti Elettrici S.r.l.", "Roma", "Via Appia Nuova 145, 00183 Roma RM, Italia"),
    ("Verdi Idraulica", "Verdi Idraulica S.r.l.", "Torino", "Corso Galileo Ferraris 18, 10121 Torino TO, Italia"),
    ("Ferrari Ristrutturazioni", "Ferrari Ristrutturazioni S.r.l.", "Napoli", "Via Toledo 88, 80134 Napoli NA, Italia"),
    ("Conti Energia", "Conti Energia S.r.l.", "Bologna", "Via Indipendenza 22, 40121 Bologna BO, Italia"),
    ("Moretti Cantieri", "Moretti Cantieri S.r.l.", "Verona", "Corso Porta Nuova 54, 37122 Verona VR, Italia"),
    ("Lombardi Service", "Lombardi Service S.r.l.", "Firenze", "Via de' Tornabuoni 31, 50123 Firenze FI, Italia"),
    ("Greco Infrastrutture", "Greco Infrastrutture S.r.l.", "Genova", "Via XX Settembre 15, 16121 Genova GE, Italia"),
    ("Romano Tecnica", "Romano Tecnica S.r.l.", "Padova", "Piazza dei Signori 6, 35139 Padova PD, Italia"),
    ("De Luca Opere", "De Luca Opere S.r.l.", "Bari", "Corso Vittorio Emanuele II 102, 70122 Bari BA, Italia"),
    ("Costa Facility", "Costa Facility S.r.l.", "Milano", "Via Torino 55, 20123 Milano MI, Italia"),
    ("Gallo Manutenzioni", "Gallo Manutenzioni S.r.l.", "Roma", "Via Cavour 120, 00184 Roma RM, Italia"),
    ("Marino Edile", "Marino Edile S.r.l.", "Torino", "Via Po 16, 10123 Torino TO, Italia"),
    ("Vitale Impianti", "Vitale Impianti S.r.l.", "Napoli", "Via Chiaia 44, 80132 Napoli NA, Italia"),
    ("Conti Urban", "Conti Urban S.r.l.", "Bologna", "Via Marconi 7, 40122 Bologna BO, Italia"),
    ("Rizzo Restauri", "Rizzo Restauri S.r.l.", "Verona", "Piazza Bra 9, 37121 Verona VR, Italia"),
    ("Neri Cantieri", "Neri Cantieri S.r.l.", "Firenze", "Via Calzaiuoli 20, 50122 Firenze FI, Italia"),
    ("Ferrara Building", "Ferrara Building S.r.l.", "Genova", "Via Garibaldi 24, 16124 Genova GE, Italia"),
    ("Lupo Energia", "Lupo Energia S.r.l.", "Padova", "Via Roma 81, 35122 Padova PD, Italia"),
    ("Sanna Costruzioni", "Sanna Costruzioni S.r.l.", "Bari", "Via Sparano 67, 70121 Bari BA, Italia"),
]

SKILL_CATALOG = [
    "Maçonnerie générale",
    "Coffrage et béton armé",
    "Carrelage et revêtements",
    "Peinture et finition",
    "Plomberie sanitaire",
    "Installation sanitaire",
    "Électricité résidentielle",
    "Électricité industrielle",
    "Câblage courant faible",
    "Lecture de plans",
    "Sécurité chantier",
    "Gestion d'équipe",
]

DEPARTMENT_SKILLS = {
    "construction": ["Maçonnerie générale", "Coffrage et béton armé", "Carrelage et revêtements", "Peinture et finition"],
    "electricity": ["Électricité résidentielle", "Électricité industrielle", "Câblage courant faible", "Lecture de plans"],
    "plumbing": ["Plomberie sanitaire", "Installation sanitaire", "Lecture de plans", "Sécurité chantier"],
    "management": ["Gestion d'équipe", "Lecture de plans", "Sécurité chantier"],
    "finance": ["Gestion d'équipe", "Lecture de plans"],
    "hr": ["Gestion d'équipe", "Sécurité chantier"],
}

PROJECT_TEMPLATES = [
    {
        "suffix": "chantier en cours",
        "status": "active",
        "domain": "construction",
        "start_offset": -120,
        "duration": 90,
        "active_team": True,
    },
    {
        "suffix": "maintenance site",
        "status": "active",
        "domain": "electricity",
        "start_offset": -90,
        "duration": 75,
        "active_team": True,
    },
    {
        "suffix": "travaux plomberie",
        "status": "active",
        "domain": "plumbing",
        "start_offset": -60,
        "duration": 60,
        "active_team": True,
    },
    {
        "suffix": "réfection finition",
        "status": "active",
        "domain": "construction",
        "start_offset": -45,
        "duration": 45,
        "active_team": True,
    },
    {
        "suffix": "projet futur lot 1",
        "status": "planning",
        "domain": "electricity",
        "start_offset": 30,
        "duration": 90,
        "active_team": False,
    },
    {
        "suffix": "projet futur lot 2",
        "status": "planning",
        "domain": "plumbing",
        "start_offset": 60,
        "duration": 120,
        "active_team": False,
    },
    {
        "suffix": "projet futur lot 3",
        "status": "planning",
        "domain": "construction",
        "start_offset": 90,
        "duration": 150,
        "active_team": False,
    },
    {
        "suffix": "livré et terminé",
        "status": "completed",
        "domain": "construction",
        "start_offset": -240,
        "duration": 110,
        "active_team": True,
    },
    {
        "suffix": "livré et terminé 2",
        "status": "completed",
        "domain": "electricity",
        "start_offset": -180,
        "duration": 95,
        "active_team": True,
    },
    {
        "suffix": "suivi de clôture",
        "status": "active",
        "domain": "plumbing",
        "start_offset": -30,
        "duration": 50,
        "active_team": True,
    },
]


@dataclass
class EmployeeSeed:
    email: str
    first_name: str
    last_name: str
    role: str
    org_id: int
    username: str
    manager_id: int | None = None
    department: str | None = None
    hourly_cost: Decimal | None = None
    phone: str | None = None
    address: str | None = None
    mission_free: bool = False


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=10)).decode()


def normalize_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    token = normalized.lower().replace("'", "").replace(" ", ".")
    token = "".join(ch for ch in token if ch.isalnum() or ch in {".", "_", "-"})
    return token.strip("._-")


def make_email(prefix: str, index: int) -> str:
    return f"{prefix}{index:02d}@timelyna.it"


def make_username(prefix: str, index: int) -> str:
    return f"{prefix}{index:02d}"


def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def project_code(client_idx: int, template_idx: int) -> str:
    return f"C{client_idx:02d}-P{template_idx + 1:02d}"


def project_name(client_name: str, template_suffix: str) -> str:
    return f"{client_name} - {template_suffix}"


async def truncate_database(session) -> None:
    table_names = [f'"{table.name}"' for table in Base.metadata.sorted_tables]
    if not table_names:
        return
    await session.execute(text(f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE"))
    await session.commit()


def employee_skill_names(role: str, department: str | None) -> list[str]:
    if role in {"manager", "admin"}:
        return DEPARTMENT_SKILLS["management"]
    if role == "finance":
        return DEPARTMENT_SKILLS["finance"]
    if role == "payroll":
        return DEPARTMENT_SKILLS["hr"]
    if department == "electricity":
        return DEPARTMENT_SKILLS["electricity"]
    if department == "plumbing":
        return DEPARTMENT_SKILLS["plumbing"]
    return DEPARTMENT_SKILLS["construction"]


def project_skill_names(domain: str) -> list[str]:
    if domain == "electricity":
        return ["Électricité résidentielle", "Électricité industrielle"]
    if domain == "plumbing":
        return ["Plomberie sanitaire", "Installation sanitaire"]
    return ["Maçonnerie générale", "Carrelage et revêtements"]


def employee_department(org_index: int, seq: int) -> str:
    pool = ["construction", "electricity", "plumbing"]
    return pool[(org_index + seq) % len(pool)]


async def seed_orgs(db):
    orgs = []
    for name in ORG_NAMES:
        org = Organization(org_name=name)
        db.add(org)
        orgs.append(org)
    await db.flush()

    for org in orgs:
        db.add(
            OrgSettings(
                org_id=org.org_id,
                org_name=org.org_name,
                standard_hours_per_day=8.0,
                max_hours_per_day=12.0,
                overtime_rate_multiplier=1.25,
                travel_rate_multiplier=0.50,
                default_currency="EUR",
            )
        )
    await db.flush()
    return orgs


async def seed_employees(db, orgs):
    created: dict[str, list[Employee]] = {"admin": [], "manager": [], "finance": [], "payroll": [], "employee": []}
    mission_free_flags: list[bool] = []

    # Admins
    for idx in range(1, 4):
        first = fake.first_name()
        last = fake.last_name()
        emp = Employee(
            email=make_email("admin", idx),
            first_name=first,
            last_name=last,
            password_hash=hash_pw(ROLE_PASSWORDS["admin"]),
            role="admin",
            employment_status="active",
            org_id=orgs[0].org_id,
            username=make_username("admin", idx),
            department="Management",
            must_change_password=False,
            annual_leave_days=30,
            preferred_language="fr",
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=TODAY - timedelta(days=900 + idx * 7),
        )
        db.add(emp)
        created["admin"].append(emp)
    await db.flush()

    # Managers: 2 per org, first 10 are org leads.
    for idx in range(1, 21):
        org = orgs[(idx - 1) % len(orgs)]
        role_title = "Lead" if idx <= 10 else "Supervisor"
        first = fake.first_name()
        last = fake.last_name()
        dept = employee_department(org.org_id, idx)
        emp = Employee(
            email=make_email("manager", idx),
            first_name=first,
            last_name=last,
            password_hash=hash_pw(ROLE_PASSWORDS["manager"]),
            role="manager",
            employment_status="active",
            org_id=org.org_id,
            username=make_username("manager", idx),
            department=f"{role_title} {dept}",
            hourly_cost=Decimal("58.00") + Decimal(str(idx % 5)),
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=TODAY - timedelta(days=700 + idx * 5),
            manager_id=created["admin"][idx % len(created["admin"])].employee_id,
        )
        db.add(emp)
        created["manager"].append(emp)
    await db.flush()

    # Finance and payroll/RH.
    for idx in range(1, 6):
        first = fake.first_name()
        last = fake.last_name()
        emp = Employee(
            email=make_email("finance", idx),
            first_name=first,
            last_name=last,
            password_hash=hash_pw(ROLE_PASSWORDS["finance"]),
            role="finance",
            employment_status="active",
            org_id=orgs[(idx - 1) % len(orgs)].org_id,
            username=make_username("finance", idx),
            department="Finance",
            hourly_cost=Decimal("40.00") + Decimal(str(idx)),
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=TODAY - timedelta(days=500 + idx * 11),
            manager_id=created["admin"][0].employee_id,
        )
        db.add(emp)
        created["finance"].append(emp)
    for idx in range(1, 6):
        first = fake.first_name()
        last = fake.last_name()
        emp = Employee(
            email=make_email("payroll", idx),
            first_name=first,
            last_name=last,
            password_hash=hash_pw(ROLE_PASSWORDS["payroll"]),
            role="payroll",
            employment_status="active",
            org_id=orgs[(idx + 1) % len(orgs)].org_id,
            username=make_username("payroll", idx),
            department="RH",
            hourly_cost=Decimal("38.00") + Decimal(str(idx)),
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=TODAY - timedelta(days=450 + idx * 11),
            manager_id=created["admin"][1].employee_id,
        )
        db.add(emp)
        created["payroll"].append(emp)

    # Employees: 67 total, last 12 are mission-free.
    for idx in range(1, 68):
        org = orgs[(idx - 1) % len(orgs)]
        manager_pool = [m for m in created["manager"] if m.org_id == org.org_id]
        manager = manager_pool[(idx - 1) % len(manager_pool)]
        mission_free = idx > 55
        department = employee_department(org.org_id, idx)
        first = fake.first_name()
        last = fake.last_name()
        emp = Employee(
            email=make_email("employee", idx),
            first_name=first,
            last_name=last,
            password_hash=hash_pw(ROLE_PASSWORDS["employee"]),
            role="employee",
            employment_status="active",
            org_id=org.org_id,
            username=make_username("employee", idx),
            department=department,
            hourly_cost=Decimal("27.00") + Decimal(str(idx % 10)),
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=TODAY - timedelta(days=120 + idx * 9),
            manager_id=manager.employee_id,
        )
        db.add(emp)
        created["employee"].append(emp)
        mission_free_flags.append(mission_free)

    await db.flush()

    mission_free_ids: set[int] = set()
    for employee, is_mission_free in zip(created["employee"], mission_free_flags, strict=True):
        if is_mission_free:
            mission_free_ids.add(employee.employee_id)

    # Link organizations to their lead manager.
    for org, manager in zip(orgs, created["manager"][:10], strict=True):
        org.manager_id = manager.employee_id

    await db.flush()
    return created, mission_free_ids


async def seed_clients(db, orgs):
    clients = []
    for idx, (client_name, company_name, city, address) in enumerate(CLIENTS, start=1):
        client = Client(
            client_name=client_name,
            company_name=company_name,
            email=f"billing@{normalize_token(client_name)}.it",
            phone=fake.phone_number(),
            address=address,
            default_billing_rate=Decimal("145.00") + Decimal(str((idx % 5) * 5)),
            currency="EUR",
            tax_id=f"IT{idx:011d}",
            client_status="active",
        )
        db.add(client)
        clients.append({"client": client, "org": orgs[(idx - 1) // 2], "city": city})
    await db.flush()
    return clients


async def seed_skills(db, orgs):
    skill_map: dict[tuple[int, str], SkillRate] = {}
    for org in orgs:
        for skill_name in SKILL_CATALOG:
            skill = SkillRate(
                org_id=org.org_id,
                skill_name=skill_name,
                billing_rate=Decimal("42.00") + Decimal(str((len(skill_name) % 9) * 3)),
                description=skill_name,
            )
            db.add(skill)
            skill_map[(org.org_id, skill_name)] = skill
    await db.flush()
    return skill_map


async def seed_employee_skills(db, employees, skill_map):
    for employee in employees:
        skill_names = employee_skill_names(employee.role, employee.department)
        chosen = skill_names[:]
        if employee.role == "employee":
            if employee.department == "electricity":
                chosen += ["Sécurité chantier"]
            elif employee.department == "plumbing":
                chosen += ["Sécurité chantier"]
        for skill_name in dict.fromkeys(chosen):
            db.add(
                EmployeeSkill(
                    employee_id=employee.employee_id,
                    skill_rate_id=skill_map[(employee.org_id, skill_name)].id,
                )
            )
    await db.flush()


def pick_team_members(pool: list[Employee], size: int) -> list[Employee]:
    if not pool:
        return []
    size = min(size, len(pool))
    return random.sample(pool, size)


async def seed_projects(db, orgs, clients, employees, skill_map, mission_free_ids):
    active_projects: list[Project] = []
    project_assignments: dict[int, list[int]] = {}
    primary_projects: dict[int, int] = {}

    employees_by_org: dict[int, list[Employee]] = {org.org_id: [] for org in orgs}
    for employee in employees["employee"]:
        employees_by_org[employee.org_id].append(employee)

    managers_by_org: dict[int, list[Employee]] = {org.org_id: [] for org in orgs}
    for manager in employees["manager"]:
        managers_by_org[manager.org_id].append(manager)

    for client_index, client_info in enumerate(clients, start=1):
        org = client_info["org"]
        client = client_info["client"]
        org_workers = [e for e in employees_by_org[org.org_id] if e.employee_id not in mission_free_ids]
        org_managers = managers_by_org[org.org_id]

        for template_index, template in enumerate(PROJECT_TEMPLATES):
            status = template["status"]
            start_date = TODAY + timedelta(days=template["start_offset"])
            end_date = start_date + timedelta(days=template["duration"])
            manager = org_managers[template_index % len(org_managers)]
            project = Project(
                client_id=client.client_id,
                project_name=project_name(client.client_name, template["suffix"]),
                project_code=project_code(client_index, template_index),
                description=f"{client.client_name} - {template['suffix']}",
                status=status,
                start_date=start_date,
                end_date=end_date,
                budget_hours=Decimal(str(template["duration"] * 6)),
                budget_amount=Decimal(str(template["duration"] * 6 * 155)),
                billing_rate=Decimal("155.00") + Decimal(str(template_index % 5)),
                manager_id=manager.employee_id,
                team_members=[],
            )
            db.add(project)
            await db.flush()

            skill_names = project_skill_names(template["domain"])
            for skill_name in skill_names:
                db.add(
                    ProjectRequiredSkill(
                        project_id=project.project_id,
                        skill_rate_id=skill_map[(org.org_id, skill_name)].id,
                        quantity=1,
                    )
                )

            if template["active_team"]:
                team_candidates = org_workers[:]
                team_candidates.sort(key=lambda employee: employee.employee_id)
                team_members = pick_team_members(team_candidates, 4)
                if not team_members:
                    team_members = [manager]
                team_ids = [manager.employee_id] + [member.employee_id for member in team_members]
                project.team_members = team_ids
                for member in team_members:
                    db.add(
                        ProjectTeamMember(
                            project_id=project.project_id,
                            employee_id=member.employee_id,
                            skill_rate_id=skill_map[(member.org_id, employee_skill_names(member.role, member.department)[0])].id,
                            custom_rate=None,
                        )
                    )
                    project_assignments.setdefault(member.employee_id, []).append(project.project_id)
                    primary_projects.setdefault(member.employee_id, project.project_id)
                db.add(
                    ProjectTeamMember(
                        project_id=project.project_id,
                        employee_id=manager.employee_id,
                        skill_rate_id=skill_map[(manager.org_id, employee_skill_names(manager.role, manager.department)[0])].id,
                        custom_rate=Decimal("75.00"),
                    )
                )
                active_projects.append(project)

    await db.flush()
    return active_projects, project_assignments, primary_projects


async def seed_timesheets_and_approvals(db, employees, projects_by_id, primary_projects, mission_free_ids):
    week_starts = [monday_of_week(TODAY - timedelta(days=7 * offset)) for offset in (4, 3, 2, 1)]
    created_entries = 0
    created_approvals = 0
    active_workers = [employee for employee in employees["employee"] if employee.employee_id in primary_projects and employee.employee_id not in mission_free_ids]

    for employee in active_workers[:50]:
        project = projects_by_id[primary_projects[employee.employee_id]]
        manager_id = employee.manager_id
        for week_index, week_start in enumerate(week_starts):
            approval_status = "approved" if week_index < 2 else "submitted"
            approval = Approval(
                employee_id=employee.employee_id,
                manager_id=manager_id,
                week_start=week_start,
                status=approval_status,
                notes="Seed de demonstration",
                rejection_reason=None,
                decided_at=(datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=6, hours=18)) if approval_status == "approved" else None,
            )
            db.add(approval)
            created_approvals += 1

            for day_offset, entry_type, hours in [
                (0, "normal", Decimal("8.00")),
                (1, "normal", Decimal("7.50")),
                (2, "travel", Decimal("1.50")),
            ]:
                status = "approved" if week_index < 2 else ("submitted" if week_index == 2 else "draft")
                db.add(
                    TimesheetEntry(
                        employee_id=employee.employee_id,
                        project_id=project.project_id,
                        work_date=week_start + timedelta(days=day_offset),
                        hours_worked=hours,
                        description=f"Pointage {project.project_name} - semaine {week_start.isoformat()}",
                        task_type="chantier",
                        entry_type=entry_type,
                        billable_flag=True,
                        billing_rate=project.billing_rate,
                        status=status,
                        notes=None,
                        submitted_at=(datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=8)) if status in {"submitted", "approved"} else None,
                        approved_at=(datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=6, hours=18)) if status == "approved" else None,
                        proxy_admin_id=None,
                    )
                )
                created_entries += 1

    await db.flush()
    return created_entries, created_approvals


async def seed_absences(db, employees):
    created = 0
    selected = employees["employee"][:20] + employees["manager"][:5] + employees["finance"][:3] + employees["payroll"][:2]
    for idx, employee in enumerate(selected, start=1):
        absence_type = "cp" if idx % 2 else "sick_leave"
        status = "approved" if idx % 3 else "pending"
        start_date = TODAY - timedelta(days=14 + idx * 2)
        duration = 2 if absence_type == "cp" else 4
        db.add(
            Absence(
                employee_id=employee.employee_id,
                absence_type=absence_type,
                start_date=start_date,
                end_date=start_date + timedelta(days=duration),
                notes=f"Seed absence {absence_type} #{idx}",
                status=status,
                rejection_reason=None,
                approved_by=employee.manager_id if status == "approved" else None,
                approved_at=(datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12)) if status == "approved" else None,
            )
        )
        created += 1
    await db.flush()
    return created


async def main() -> None:
    session_factory = _get_session_factory()

    async with session_factory() as db:
        print("[1/6] Purge complete de la base...")
        await truncate_database(db)

        print("[2/6] Creation des organisations et parametres...")
        orgs = await seed_orgs(db)

        print("[3/6] Creation des employes, managers, finance, RH et admins...")
        employees, mission_free_ids = await seed_employees(db, orgs)

        print("[4/6] Creation des clients et competences...")
        clients = await seed_clients(db, orgs)
        skill_map = await seed_skills(db, orgs)
        await seed_employee_skills(db, [*employees["admin"], *employees["manager"], *employees["finance"], *employees["payroll"], *employees["employee"]], skill_map)

        print("[5/6] Creation des projets, equipes et missions futures...")
        active_projects, project_assignments, primary_projects = await seed_projects(db, orgs, clients, employees, skill_map, mission_free_ids)
        projects_by_id = {project.project_id: project for project in active_projects}

        print("[6/6] Creation des pointages, approbations et absences...")
        timesheet_count, approval_count = await seed_timesheets_and_approvals(db, employees, projects_by_id, primary_projects, mission_free_ids)
        absence_count = await seed_absences(db, employees)

        await db.commit()

    mission_free = [employee.email for employee in employees["employee"] if employee.employee_id in mission_free_ids]
    print("\nSeed termine avec succes.")
    print(f"Organizations: {len(orgs)}")
    print(f"Clients: {len(clients)}")
    print(f"Projects: {len(clients) * len(PROJECT_TEMPLATES)}")
    print(f"Employees: {sum(len(group) for group in employees.values())}")
    print(f"Managers: {len(employees['manager'])}")
    print(f"Admins: {len(employees['admin'])}")
    print(f"Finance: {len(employees['finance'])}")
    print(f"RH/Payroll: {len(employees['payroll'])}")
    print(f"Pointages: {timesheet_count}")
    print(f"Approvals: {approval_count}")
    print(f"Absences: {absence_count}")
    print(f"Employes sans missions: {len(mission_free)}")
    print("\nComptes de connexion:")
    for role, password in ROLE_PASSWORDS.items():
        print(f"  {role}: {password}")


if __name__ == "__main__":
    asyncio.run(main())