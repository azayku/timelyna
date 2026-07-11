from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, "/app")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://timelyna:changeme@postgres:5432/timelyna",
)

ADMIN_PASSWORD = "AdminIt123!"
MANAGER_PASSWORD = "ManagerIt123!"
FINANCE_PASSWORD = "FinanceIt123!"
EMPLOYEE_PASSWORD = "EmployeeIt123!"


@dataclass(frozen=True)
class OrgDef:
    org_id: int
    name: str


@dataclass(frozen=True)
class PersonDef:
    email: str
    first_name: str
    last_name: str
    role: str
    org_id: int
    username: str
    password: str
    manager_email: str | None = None
    department: str | None = None
    hourly_cost: Decimal | None = None


@dataclass(frozen=True)
class ClientDef:
    client_name: str
    company_name: str
    email: str
    phone: str
    address: str
    billing_rate: Decimal
    currency: str = "EUR"


@dataclass(frozen=True)
class ProjectDef:
    project_code: str
    project_name: str
    client_name: str
    manager_email: str
    start_date: date
    billing_rate: Decimal
    budget_hours: Decimal
    budget_amount: Decimal
    required_skills: list[str]
    team_emails: list[str]


ORGS = [
    OrgDef(1, "Impresa Alfa Milano S.r.l."),
    OrgDef(2, "Roma Energia & Impianti S.r.l."),
    OrgDef(3, "Torino Edilizia Nord S.r.l."),
    OrgDef(4, "Napoli Ristrutturazioni Sud S.r.l."),
]

PEOPLE = [
    PersonDef("elena.conti@timelyna.it", "Elena", "Conti", "admin", 1, "elena.conti", ADMIN_PASSWORD, department="Management"),
    PersonDef("chiara.marino@timelyna.it", "Chiara", "Marino", "admin", 1, "chiara.marino", ADMIN_PASSWORD, department="Management"),
    PersonDef("sofia.moretti@timelyna.it", "Sofia", "Moretti", "finance", 1, "sofia.moretti", FINANCE_PASSWORD, department="Finance"),
    PersonDef("luca.ferri@timelyna.it", "Luca", "Ferri", "manager", 1, "luca.ferri", MANAGER_PASSWORD, department="Cantiere", hourly_cost=Decimal("58.00")),
    PersonDef("marco.bianchi@timelyna.it", "Marco", "Bianchi", "manager", 2, "marco.bianchi", MANAGER_PASSWORD, department="Impianti", hourly_cost=Decimal("62.00")),
    PersonDef("giovanni.romano@timelyna.it", "Giovanni", "Romano", "manager", 3, "giovanni.romano", MANAGER_PASSWORD, department="Edilizia", hourly_cost=Decimal("60.00")),
    PersonDef("paolo.greco@timelyna.it", "Paolo", "Greco", "employee", 1, "paolo.greco", EMPLOYEE_PASSWORD, manager_email="luca.ferri@timelyna.it", department="Elettricità", hourly_cost=Decimal("34.00")),
    PersonDef("salvatore.neri@timelyna.it", "Salvatore", "Neri", "employee", 1, "salvatore.neri", EMPLOYEE_PASSWORD, manager_email="luca.ferri@timelyna.it", department="Plomberie", hourly_cost=Decimal("32.00")),
    PersonDef("davide.ferrara@timelyna.it", "Davide", "Ferrara", "employee", 1, "davide.ferrara", EMPLOYEE_PASSWORD, manager_email="luca.ferri@timelyna.it", department="Maçonnerie", hourly_cost=Decimal("33.50")),
    PersonDef("alessandro.romano@timelyna.it", "Alessandro", "Romano", "employee", 2, "alessandro.romano", EMPLOYEE_PASSWORD, manager_email="marco.bianchi@timelyna.it", department="Elettricità", hourly_cost=Decimal("35.00")),
    PersonDef("francesco.vitale@timelyna.it", "Francesco", "Vitale", "employee", 2, "francesco.vitale", EMPLOYEE_PASSWORD, manager_email="marco.bianchi@timelyna.it", department="Plomberie", hourly_cost=Decimal("31.00")),
    PersonDef("andrea.lombardi@timelyna.it", "Andrea", "Lombardi", "employee", 2, "andrea.lombardi", EMPLOYEE_PASSWORD, manager_email="marco.bianchi@timelyna.it", department="Carrelage", hourly_cost=Decimal("36.00")),
    PersonDef("simone.costa@timelyna.it", "Simone", "Costa", "employee", 3, "simone.costa", EMPLOYEE_PASSWORD, manager_email="giovanni.romano@timelyna.it", department="Installation", hourly_cost=Decimal("34.50")),
    PersonDef("matteo.rizzo@timelyna.it", "Matteo", "Rizzo", "employee", 3, "matteo.rizzo", EMPLOYEE_PASSWORD, manager_email="giovanni.romano@timelyna.it", department="Finition", hourly_cost=Decimal("32.50")),
    PersonDef("nicola.gallo@timelyna.it", "Nicola", "Gallo", "employee", 4, "nicola.gallo", EMPLOYEE_PASSWORD, manager_email="luca.ferri@timelyna.it", department="Courant faible", hourly_cost=Decimal("33.00")),
    PersonDef("giorgio.deluca@timelyna.it", "Giorgio", "De Luca", "employee", 4, "giorgio.deluca", EMPLOYEE_PASSWORD, manager_email="marco.bianchi@timelyna.it", department="Câblage", hourly_cost=Decimal("34.00")),
]

CLIENTS = [
    ClientDef(
        "Rossi Costruzioni",
        "Rossi Costruzioni S.r.l.",
        "billing@rossicostruzioni.it",
        "+39 02 1234 5678",
        "Via Roma 12, 20121 Milano MI, Italia",
        Decimal("145.00"),
    ),
    ClientDef(
        "Bianchi Impianti",
        "Bianchi Impianti Elettrici S.p.A.",
        "amministrazione@bianchiimpianti.it",
        "+39 06 9876 5432",
        "Via Appia Nuova 145, 00183 Roma RM, Italia",
        Decimal("155.00"),
    ),
    ClientDef(
        "Verdi Idraulica",
        "Verdi Idraulica S.r.l.",
        "billing@verdiidraulica.it",
        "+39 011 234 5678",
        "Corso Galileo Ferraris 18, 10121 Torino TO, Italia",
        Decimal("135.00"),
    ),
    ClientDef(
        "Ferrari Ristrutturazioni",
        "Ferrari Ristrutturazioni S.r.l.",
        "contabilita@ferrariristrutturazioni.it",
        "+39 081 555 1212",
        "Via Toledo 88, 80134 Napoli NA, Italia",
        Decimal("160.00"),
    ),
    ClientDef(
        "Conti Energia",
        "Conti Energia S.r.l.",
        "billing@conti-energia.it",
        "+39 051 444 3322",
        "Via Indipendenza 22, 40121 Bologna BO, Italia",
        Decimal("150.00"),
    ),
]

PROJECTS = [
    ProjectDef(
        "MIL-EL-2026-01",
        "Rifacimento impianto elettrico Milano Centro",
        "Bianchi Impianti",
        "luca.ferri@timelyna.it",
        date(2026, 9, 1),
        Decimal("160.00"),
        Decimal("180.00"),
        Decimal("28800.00"),
        ["Électricité résidentielle", "Lecture de plans", "Câblage courant faible"],
        ["paolo.greco@timelyna.it", "davide.ferrara@timelyna.it", "nicola.gallo@timelyna.it"],
    ),
    ProjectDef(
        "ROM-PL-2026-01",
        "Modernisation plomberie condominio Roma",
        "Verdi Idraulica",
        "marco.bianchi@timelyna.it",
        date(2026, 9, 15),
        Decimal("155.00"),
        Decimal("140.00"),
        Decimal("21700.00"),
        ["Plomberie sanitaire", "Installation sanitaire", "Lecture de plans"],
        ["salvatore.neri@timelyna.it", "francesco.vitale@timelyna.it"],
    ),
    ProjectDef(
        "TOR-ED-2026-01",
        "Rénovation façade et gros œuvre Turin",
        "Rossi Costruzioni",
        "giovanni.romano@timelyna.it",
        date(2026, 10, 1),
        Decimal("170.00"),
        Decimal("220.00"),
        Decimal("37400.00"),
        ["Maçonnerie générale", "Coffrage et béton armé", "Carrelage et revêtements"],
        ["andrea.lombardi@timelyna.it", "simone.costa@timelyna.it", "matteo.rizzo@timelyna.it"],
    ),
    ProjectDef(
        "NAP-RI-2026-01",
        "Ristrutturazione villa Napoli Sud",
        "Ferrari Ristrutturazioni",
        "luca.ferri@timelyna.it",
        date(2026, 11, 1),
        Decimal("165.00"),
        Decimal("200.00"),
        Decimal("33000.00"),
        ["Peinture et finition", "Carrelage et revêtements", "Installation sanitaire"],
        ["giorgio.deluca@timelyna.it", "simone.costa@timelyna.it"],
    ),
    ProjectDef(
        "BOL-DO-2026-01",
        "Automazione domotica Bologna",
        "Conti Energia",
        "marco.bianchi@timelyna.it",
        date(2026, 12, 1),
        Decimal("175.00"),
        Decimal("120.00"),
        Decimal("21000.00"),
        ["Électricité industrielle", "Câblage courant faible", "Lecture de plans"],
        ["paolo.greco@timelyna.it", "alessandro.romano@timelyna.it", "nicola.gallo@timelyna.it"],
    ),
    ProjectDef(
        "MIL-SA-2026-01",
        "Réfection sanitaires Milan Sud",
        "Verdi Idraulica",
        "giovanni.romano@timelyna.it",
        date(2026, 10, 15),
        Decimal("148.00"),
        Decimal("96.00"),
        Decimal("14208.00"),
        ["Plomberie sanitaire", "Installation sanitaire"],
        ["salvatore.neri@timelyna.it", "francesco.vitale@timelyna.it"],
    ),
]

SKILLS = [
    ("Maçonnerie générale", Decimal("48.00")),
    ("Coffrage et béton armé", Decimal("52.00")),
    ("Carrelage et revêtements", Decimal("45.00")),
    ("Plomberie sanitaire", Decimal("50.00")),
    ("Installation sanitaire", Decimal("49.00")),
    ("Électricité résidentielle", Decimal("55.00")),
    ("Électricité industrielle", Decimal("60.00")),
    ("Câblage courant faible", Decimal("53.00")),
    ("Lecture de plans", Decimal("42.00")),
    ("Peinture et finition", Decimal("44.00")),
]

EMPLOYEE_SKILL_MAP = {
    "paolo.greco@timelyna.it": ["Électricité résidentielle", "Lecture de plans"],
    "salvatore.neri@timelyna.it": ["Plomberie sanitaire", "Installation sanitaire"],
    "davide.ferrara@timelyna.it": ["Maçonnerie générale", "Carrelage et revêtements"],
    "alessandro.romano@timelyna.it": ["Électricité industrielle", "Câblage courant faible"],
    "francesco.vitale@timelyna.it": ["Plomberie sanitaire", "Lecture de plans"],
    "andrea.lombardi@timelyna.it": ["Maçonnerie générale", "Peinture et finition"],
    "simone.costa@timelyna.it": ["Installation sanitaire", "Carrelage et revêtements"],
    "matteo.rizzo@timelyna.it": ["Peinture et finition", "Lecture de plans"],
    "nicola.gallo@timelyna.it": ["Câblage courant faible", "Électricité résidentielle"],
    "giorgio.deluca@timelyna.it": ["Électricité industrielle", "Lecture de plans"],
}

def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=10)).decode()


def slug_username(first_name: str, last_name: str) -> str:
    return f"{first_name.lower()}.{last_name.lower()}".replace(" ", "")[:50]


def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def get_one(db: AsyncSession, model, **filters):
    result = await db.execute(select(model).filter_by(**filters))
    return result.scalar_one_or_none()


async def ensure_organization(db: AsyncSession, org_def: OrgDef, manager_id: int | None = None):
    from app.models.organization import Organization

    org = await get_one(db, Organization, org_id=org_def.org_id)
    if org is None:
        org = Organization(org_id=org_def.org_id, org_name=org_def.name, manager_id=manager_id)
        db.add(org)
        await db.flush()
    else:
        org.org_name = org_def.name
        org.manager_id = manager_id
    return org


async def ensure_org_settings(db: AsyncSession, org_def: OrgDef):
    from app.models.org_settings import OrgSettings

    settings = await get_one(db, OrgSettings, org_id=org_def.org_id)
    if settings is None:
        settings = OrgSettings(org_id=org_def.org_id, org_name=org_def.name)
        db.add(settings)
        await db.flush()
    else:
        settings.org_name = org_def.name
    return settings


async def ensure_employee(db: AsyncSession, person: PersonDef):
    from app.models.employee import Employee

    employee = await get_one(db, Employee, email=person.email)
    manager_id = None
    if person.manager_email:
        manager = await get_one(db, Employee, email=person.manager_email)
        manager_id = manager.employee_id if manager else None

    payload = dict(
        email=person.email,
        first_name=person.first_name,
        last_name=person.last_name,
        password_hash=hash_pw(person.password),
        role=person.role,
        employment_status="active",
        org_id=person.org_id,
        username=person.username,
        must_change_password=True,
        manager_id=manager_id,
        department=person.department,
        hourly_cost=person.hourly_cost,
    )

    if employee is None:
        employee = Employee(**payload)
        db.add(employee)
        await db.flush()
    else:
        for key, value in payload.items():
            setattr(employee, key, value)
    return employee


async def ensure_client(db: AsyncSession, client_def: ClientDef):
    from app.models.client import Client

    client = await get_one(db, Client, email=client_def.email)
    if client is None:
        client = Client(
            client_name=client_def.client_name,
            company_name=client_def.company_name,
            email=client_def.email,
            phone=client_def.phone,
            address=client_def.address,
            default_billing_rate=client_def.billing_rate,
            currency=client_def.currency,
            client_status="active",
        )
        db.add(client)
        await db.flush()
    else:
        client.client_name = client_def.client_name
        client.company_name = client_def.company_name
        client.phone = client_def.phone
        client.address = client_def.address
        client.default_billing_rate = client_def.billing_rate
        client.currency = client_def.currency
        client.client_status = "active"
    return client


async def ensure_skill_rate(db: AsyncSession, org_id: int, skill_name: str, billing_rate: Decimal):
    from app.models.skill_rate import SkillRate

    skill = await db.execute(select(SkillRate).where(SkillRate.org_id == org_id, SkillRate.skill_name == skill_name))
    row = skill.scalar_one_or_none()
    if row is None:
        row = SkillRate(org_id=org_id, skill_name=skill_name, billing_rate=billing_rate)
        db.add(row)
        await db.flush()
    else:
        row.billing_rate = billing_rate
    return row


async def ensure_employee_skill(db: AsyncSession, employee_id: int, skill_rate_id: int):
    from app.models.employee_skill import EmployeeSkill

    row = await db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_rate_id == skill_rate_id,
        )
    )
    existing = row.scalar_one_or_none()
    if existing is None:
        existing = EmployeeSkill(employee_id=employee_id, skill_rate_id=skill_rate_id)
        db.add(existing)
        await db.flush()
    return existing


async def ensure_project(db: AsyncSession, project_def: ProjectDef, client_id: int, manager_id: int, team_members: list[int]):
    from app.models.project import Project

    project = await get_one(db, Project, project_code=project_def.project_code)
    payload = dict(
        client_id=client_id,
        project_name=project_def.project_name,
        project_code=project_def.project_code,
        description=project_def.project_name,
        status="planning",
        start_date=project_def.start_date,
        end_date=project_def.start_date + timedelta(days=120),
        budget_hours=project_def.budget_hours,
        budget_amount=project_def.budget_amount,
        billing_rate=project_def.billing_rate,
        manager_id=manager_id,
        team_members=team_members,
    )
    if project is None:
        project = Project(**payload)
        db.add(project)
        await db.flush()
    else:
        for key, value in payload.items():
            setattr(project, key, value)
    return project


async def ensure_project_required_skill(db: AsyncSession, project_id: int, skill_rate_id: int, quantity: int = 1):
    from app.models.project_required_skill import ProjectRequiredSkill

    row = await db.execute(
        select(ProjectRequiredSkill).where(
            ProjectRequiredSkill.project_id == project_id,
            ProjectRequiredSkill.skill_rate_id == skill_rate_id,
        )
    )
    existing = row.scalar_one_or_none()
    if existing is None:
        existing = ProjectRequiredSkill(project_id=project_id, skill_rate_id=skill_rate_id, quantity=quantity)
        db.add(existing)
        await db.flush()
    else:
        existing.quantity = quantity
    return existing


async def ensure_project_team_member(db: AsyncSession, project_id: int, employee_id: int, skill_rate_id: int | None = None, custom_rate: Decimal | None = None):
    from app.models.project_team_member import ProjectTeamMember

    row = await db.execute(
        select(ProjectTeamMember).where(
            ProjectTeamMember.project_id == project_id,
            ProjectTeamMember.employee_id == employee_id,
        )
    )
    existing = row.scalar_one_or_none()
    if existing is None:
        existing = ProjectTeamMember(
            project_id=project_id,
            employee_id=employee_id,
            skill_rate_id=skill_rate_id,
            custom_rate=custom_rate,
        )
        db.add(existing)
        await db.flush()
    else:
        existing.skill_rate_id = skill_rate_id
        existing.custom_rate = custom_rate
    return existing


async def ensure_timesheet_entry(
    db: AsyncSession,
    employee_id: int,
    project_id: int,
    work_date: date,
    hours_worked: Decimal,
    description: str,
    task_type: str,
    entry_type: str,
    status: str,
    submitted_at: datetime | None = None,
    approved_at: datetime | None = None,
):
    from app.models.timesheet_entry import TimesheetEntry

    row = await db.execute(
        select(TimesheetEntry).where(
            TimesheetEntry.employee_id == employee_id,
            TimesheetEntry.project_id == project_id,
            TimesheetEntry.work_date == work_date,
            TimesheetEntry.entry_type == entry_type,
        )
    )
    entry = row.scalar_one_or_none()
    payload = dict(
        employee_id=employee_id,
        project_id=project_id,
        work_date=work_date,
        hours_worked=hours_worked,
        description=description,
        task_type=task_type,
        entry_type=entry_type,
        billable_flag=True,
        billing_rate=None,
        status=status,
        notes=None,
        submitted_at=submitted_at,
        approved_at=approved_at,
    )
    if entry is None:
        entry = TimesheetEntry(**payload)
        db.add(entry)
        await db.flush()
    else:
        for key, value in payload.items():
            setattr(entry, key, value)
    return entry


async def ensure_approval(
    db: AsyncSession,
    employee_id: int,
    manager_id: int | None,
    week_start: date,
    status: str,
    notes: str | None = None,
    rejection_reason: str | None = None,
    decided_at: datetime | None = None,
):
    from app.models.approval import Approval

    row = await db.execute(select(Approval).where(Approval.employee_id == employee_id, Approval.week_start == week_start))
    approval = row.scalar_one_or_none()
    payload = dict(
        employee_id=employee_id,
        manager_id=manager_id,
        week_start=week_start,
        status=status,
        notes=notes,
        rejection_reason=rejection_reason,
        decided_at=decided_at,
    )
    if approval is None:
        approval = Approval(**payload)
        db.add(approval)
        await db.flush()
    else:
        for key, value in payload.items():
            setattr(approval, key, value)
    return approval


async def ensure_mutation_log(
    db: AsyncSession,
    employee_id: int,
    from_org_id: int,
    to_org_id: int,
    mutated_by: int,
    reason: str,
    mutated_at: datetime,
):
    from app.models.employee_mutation_log import EmployeeMutationLog

    row = await db.execute(
        select(EmployeeMutationLog).where(
            EmployeeMutationLog.employee_id == employee_id,
            EmployeeMutationLog.from_org_id == from_org_id,
            EmployeeMutationLog.to_org_id == to_org_id,
        )
    )
    log = row.scalar_one_or_none()
    if log is None:
        log = EmployeeMutationLog(
            employee_id=employee_id,
            from_org_id=from_org_id,
            to_org_id=to_org_id,
            mutated_by=mutated_by,
            reason=reason,
            mutated_at=mutated_at,
        )
        db.add(log)
        await db.flush()
    else:
        log.mutated_by = mutated_by
        log.reason = reason
        log.mutated_at = mutated_at
    return log


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as db:
        from app.models.employee import Employee

        people_def_by_email = {person.email: person for person in PEOPLE}

        # Skip only if the demo marker already exists.
        marker = await get_one(db, Employee, email="elena.conti@timelyna.it")
        if marker is not None:
            print("Demo dataset already present — refreshing records in place.")

        # Organizations must exist before employees because employees.org_id is a foreign key.
        for org in ORGS:
            await ensure_organization(db, org, None)
            await ensure_org_settings(db, org)

        people_by_email: dict[str, Employee] = {}
        for person in PEOPLE:
            employee = await ensure_employee(db, person)
            people_by_email[person.email] = employee

        # Link organizations to managers after employees exist.
        await ensure_organization(db, ORGS[0], people_by_email["luca.ferri@timelyna.it"].employee_id)
        await ensure_organization(db, ORGS[1], people_by_email["marco.bianchi@timelyna.it"].employee_id)
        await ensure_organization(db, ORGS[2], people_by_email["giovanni.romano@timelyna.it"].employee_id)
        await ensure_organization(db, ORGS[3], None)

        # Skill rates per org, then employee skills.
        skill_rates: dict[tuple[int, str], int] = {}
        for org in ORGS:
            for skill_name, billing_rate in SKILLS:
                skill_row = await ensure_skill_rate(db, org.org_id, skill_name, billing_rate)
                skill_rates[(org.org_id, skill_name)] = skill_row.id

        for email, skill_names in EMPLOYEE_SKILL_MAP.items():
            employee = people_by_email[email]
            for skill_name in skill_names:
                skill_id = skill_rates[(employee.org_id, skill_name)]
                await ensure_employee_skill(db, employee.employee_id, skill_id)

        # Italian clients.
        clients_by_email = {}
        for client_def in CLIENTS:
            client = await ensure_client(db, client_def)
            clients_by_email[client_def.email] = client

        # Future projects + required skills + team members.
        projects_by_code = {}
        for project_def in PROJECTS:
            client = next(client for client in clients_by_email.values() if client.client_name == project_def.client_name)
            manager = people_by_email[project_def.manager_email]
            team_members = [people_by_email[email].employee_id for email in project_def.team_emails]
            if manager.employee_id not in team_members:
                team_members.insert(0, manager.employee_id)
            team_members = list(dict.fromkeys(team_members))

            project = await ensure_project(db, project_def, client.client_id, manager.employee_id, team_members)
            projects_by_code[project_def.project_code] = project

            for skill_name in project_def.required_skills:
                skill_id = skill_rates[(manager.org_id, skill_name)]
                await ensure_project_required_skill(db, project.project_id, skill_id, quantity=1)

            for email in project_def.team_emails:
                employee = people_by_email[email]
                skill_name = EMPLOYEE_SKILL_MAP[email][0]
                skill_id = skill_rates[(employee.org_id, skill_name)] if (employee.org_id, skill_name) in skill_rates else None
                await ensure_project_team_member(db, project.project_id, employee.employee_id, skill_id, custom_rate=None)

        # Mutations: three real moves between orgs.
        mutation_date = datetime(2026, 6, 18, 9, 0, tzinfo=timezone.utc)
        moves = [
            ("paolo.greco@timelyna.it", 1, 2, "Mutation vers le chantier romain"),
            ("alessandro.romano@timelyna.it", 2, 3, "Mutation vers l’équipe Nord"),
            ("simone.costa@timelyna.it", 3, 4, "Mutation vers l’agence Sud"),
        ]
        acting_admin = people_by_email["elena.conti@timelyna.it"]
        for email, from_org, to_org, reason in moves:
            employee = people_by_email[email]
            employee.org_id = to_org
            await ensure_mutation_log(db, employee.employee_id, from_org, to_org, acting_admin.employee_id, reason, mutation_date)

        # Timesheets: approved last week, pending this week, a few drafts.
        today = date(2026, 6, 20)
        last_week = monday_of_week(today - timedelta(days=7))
        this_week = monday_of_week(today)

        approved_employees = [
            "paolo.greco@timelyna.it",
            "salvatore.neri@timelyna.it",
            "davide.ferrara@timelyna.it",
            "alessandro.romano@timelyna.it",
        ]
        pending_employees = [
            "francesco.vitale@timelyna.it",
            "andrea.lombardi@timelyna.it",
            "matteo.rizzo@timelyna.it",
            "nicola.gallo@timelyna.it",
        ]
        draft_employees = [
            "giorgio.deluca@timelyna.it",
            "simone.costa@timelyna.it",
        ]

        project_cycle = [
            projects_by_code["MIL-EL-2026-01"],
            projects_by_code["ROM-PL-2026-01"],
            projects_by_code["TOR-ED-2026-01"],
            projects_by_code["NAP-RI-2026-01"],
            projects_by_code["BOL-DO-2026-01"],
            projects_by_code["MIL-SA-2026-01"],
        ]

        for idx, email in enumerate(approved_employees):
            employee = people_by_email[email]
            person_def = people_def_by_email[email]
            project = project_cycle[idx % len(project_cycle)]
            await ensure_approval(
                db,
                employee.employee_id,
                people_by_email[person_def.manager_email].employee_id if person_def.manager_email else None,
                last_week,
                "approved",
                notes="Validation automatique du lot hebdomadaire",
                decided_at=datetime(2026, 6, 19, 18, 0, tzinfo=timezone.utc),
            )
            for day_offset, hours, entry_type in [(0, Decimal("8.00"), "normal"), (1, Decimal("1.50"), "travel"), (2, Decimal("0.50"), "overtime")]:
                await ensure_timesheet_entry(
                    db,
                    employee.employee_id,
                    project.project_id,
                    last_week + timedelta(days=day_offset),
                    hours,
                    f"Chantier validé - {project.project_name} - J{day_offset+1}",
                    "work",
                    entry_type,
                    "approved",
                    submitted_at=datetime(2026, 6, 16, 8, 0, tzinfo=timezone.utc),
                    approved_at=datetime(2026, 6, 19, 18, 0, tzinfo=timezone.utc),
                )

        for idx, email in enumerate(pending_employees):
            employee = people_by_email[email]
            person_def = people_def_by_email[email]
            project = project_cycle[(idx + 2) % len(project_cycle)]
            await ensure_approval(
                db,
                employee.employee_id,
                people_by_email[person_def.manager_email].employee_id if person_def.manager_email else None,
                this_week,
                "pending",
                notes="En attente de validation du chef de chantier",
            )
            for day_offset, hours, entry_type in [(0, Decimal("7.50"), "normal"), (1, Decimal("0.50"), "travel"), (3, Decimal("1.00"), "overtime")]:
                await ensure_timesheet_entry(
                    db,
                    employee.employee_id,
                    project.project_id,
                    this_week + timedelta(days=day_offset),
                    hours,
                    f"Pointage soumis - {project.project_name} - J{day_offset+1}",
                    "work",
                    entry_type,
                    "submitted",
                    submitted_at=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
                    approved_at=None,
                )

        for idx, email in enumerate(draft_employees):
            employee = people_by_email[email]
            project = project_cycle[(idx + 4) % len(project_cycle)]
            for day_offset, hours in [(0, Decimal("4.00")), (2, Decimal("3.50"))]:
                await ensure_timesheet_entry(
                    db,
                    employee.employee_id,
                    project.project_id,
                    this_week + timedelta(days=day_offset),
                    hours,
                    f"Brouillon - {project.project_name} - J{day_offset+1}",
                    "work",
                    "normal",
                    "draft",
                    submitted_at=None,
                    approved_at=None,
                )

        # One summary approval row for each admin/manager employee to make the dataset richer.
        for email in ["luca.ferri@timelyna.it", "marco.bianchi@timelyna.it", "giovanni.romano@timelyna.it"]:
            employee = people_by_email[email]
            await ensure_approval(
                db,
                employee.employee_id,
                employee.employee_id,
                last_week,
                "approved",
                notes="Validation manager",
                decided_at=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
            )

        await db.commit()

    await engine.dispose()
    print("Seed italien bâtiment terminé avec succès.")
    print("Comptes utiles:")
    print(f"  Admin: {ADMIN_PASSWORD}")
    print(f"  Manager: {MANAGER_PASSWORD}")
    print(f"  Finance: {FINANCE_PASSWORD}")
    print(f"  Employé: {EMPLOYEE_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())