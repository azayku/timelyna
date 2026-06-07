"""
Script de seed pour test de charge - TimesheetPro
Génère des données réalistes italiennes sur 12 mois :
- 50 employés, 10 managers, 2 admins, 3 finance
- 50 clients
- 1000 projets
- Pointages sur 12 mois
- Absences (congés, maladie, etc.)

Usage:
    python seed_load_test.py
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import _get_session_factory
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.client import Client
from app.models.project import Project
from app.models.project_team_member import ProjectTeamMember
from app.models.timesheet_entry import TimesheetEntry
from app.models.absence import Absence

# Initialiser Faker avec locale italienne
fake = Faker('it_IT')

# Configuration
NUM_EMPLOYEES = 50
NUM_MANAGERS = 10
NUM_ADMINS = 2
NUM_FINANCE = 3
NUM_CLIENTS = 50
NUM_PROJECTS = 1000
MONTHS_BACK = 12

PROJECT_PREFIXES = [
    "Migrazione", "Rifacimento", "Sviluppo", "Manutenzione", "Supporto",
    "Audit", "Ottimizzazione", "Integrazione", "Formazione", "Consulenza",
    "Infrastruttura", "Sicurezza", "Performance", "Monitoraggio", "Backup",
    "API", "Frontend", "Backend", "Mobile", "Cloud"
]

PROJECT_TYPES = [
    "Web", "Mobile", "Desktop", "Cloud", "API", "Database", "Infrastruttura",
    "Sicurezza", "DevOps", "Analytics", "BI", "CRM", "ERP", "E-commerce"
]

ABSENCE_TYPES = ["cp", "maladie", "autre"]


def generate_email(first_name: str, last_name: str, domain: str = "test.it") -> str:
    """Génère un email à partir du prénom et nom."""
    # Normaliser les caractères italiens pour l'email
    first = first_name.lower().replace("à", "a").replace("è", "e").replace("é", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u").replace("'", "")
    last = last_name.lower().replace("à", "a").replace("è", "e").replace("é", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u").replace("'", "")
    return f"{first}.{last}@{domain}"


def generate_project_name() -> str:
    """Génère un nom de projet réaliste."""
    prefix = random.choice(PROJECT_PREFIXES)
    type_ = random.choice(PROJECT_TYPES)
    return f"{prefix} {type_}"


async def clear_database(session: AsyncSession):
    """Vide toutes les tables (sauf organization)."""
    print("🗑️  Nettoyage de la base de données...")
    
    # Utiliser TRUNCATE CASCADE pour éviter les problèmes de contraintes
    tables = [
        "invoice_audit_logs",
        "invoice_line_items", 
        "invoices",
        "timesheet_entries",
        "absences",
        "project_team_members",
        "projects",
        "clients",
        "employees"
    ]
    
    for table in tables:
        try:
            await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        except Exception as e:
            # Ignorer les erreurs de tables inexistantes
            if "does not exist" not in str(e):
                print(f"⚠️  Erreur lors du nettoyage de {table}: {e}")
            await session.rollback()  # Rollback pour continuer
    
    await session.commit()
    print("✅ Base de données nettoyée")


async def create_organization(session: AsyncSession) -> Organization:
    """Crée ou récupère l'organisation de test."""
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    
    if not org:
        org = Organization(
            org_name="Test Organization Italia",
            created_at=datetime.utcnow()
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)
        print(f"✅ Organisation créée: {org.org_name}")
    else:
        print(f"✅ Organisation existante: {org.org_name}")
    
    return org


async def create_employees(session: AsyncSession, org_id: int):
    """Crée les employés avec différents rôles."""
    print(f"\n👥 Création de {NUM_EMPLOYEES + NUM_MANAGERS + NUM_ADMINS + NUM_FINANCE} employés...")
    
    import bcrypt
    password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt(rounds=10)).decode()
    
    employees = []
    used_emails = set()
    
    # Admins
    for i in range(NUM_ADMINS):
        first = fake.first_name()
        last = fake.last_name()
        email = generate_email(first, last, "admin.test.it")
        
        # Éviter les doublons d'email
        counter = 1
        while email in used_emails:
            email = generate_email(first, f"{last}{counter}", "admin.test.it")
            counter += 1
        used_emails.add(email)
        
        emp = Employee(
            first_name=first,
            last_name=last,
            email=email,
            password_hash=password_hash,
            role="admin",
            org_id=org_id,
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=datetime.utcnow().date() - timedelta(days=random.randint(365, 1825)),
            employment_status="active"
        )
        employees.append(emp)
    
    # Finance
    for i in range(NUM_FINANCE):
        first = fake.first_name()
        last = fake.last_name()
        email = generate_email(first, last, "finance.test.it")
        
        counter = 1
        while email in used_emails:
            email = generate_email(first, f"{last}{counter}", "finance.test.it")
            counter += 1
        used_emails.add(email)
        
        emp = Employee(
            first_name=first,
            last_name=last,
            email=email,
            password_hash=password_hash,
            role="finance",
            org_id=org_id,
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=datetime.utcnow().date() - timedelta(days=random.randint(365, 1825)),
            employment_status="active"
        )
        employees.append(emp)
    
    # Managers
    for i in range(NUM_MANAGERS):
        first = fake.first_name()
        last = fake.last_name()
        email = generate_email(first, last, "manager.test.it")
        
        counter = 1
        while email in used_emails:
            email = generate_email(first, f"{last}{counter}", "manager.test.it")
            counter += 1
        used_emails.add(email)
        
        emp = Employee(
            first_name=first,
            last_name=last,
            email=email,
            password_hash=password_hash,
            role="manager",
            org_id=org_id,
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=datetime.utcnow().date() - timedelta(days=random.randint(365, 1825)),
            employment_status="active"
        )
        employees.append(emp)
    
    # Employees
    for i in range(NUM_EMPLOYEES):
        first = fake.first_name()
        last = fake.last_name()
        email = generate_email(first, last, f"emp{i}.test.it")
        
        counter = 1
        while email in used_emails:
            email = generate_email(first, f"{last}{counter}", f"emp{i}.test.it")
            counter += 1
        used_emails.add(email)
        
        emp = Employee(
            first_name=first,
            last_name=last,
            email=email,
            password_hash=password_hash,
            role="employee",
            org_id=org_id,
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            hire_date=datetime.utcnow().date() - timedelta(days=random.randint(30, 1825)),
            employment_status="active"
        )
        employees.append(emp)
    
    session.add_all(employees)
    await session.commit()
    
    print(f"✅ {len(employees)} employés créés")
    print(f"   - {NUM_ADMINS} admins")
    print(f"   - {NUM_FINANCE} finance")
    print(f"   - {NUM_MANAGERS} managers")
    print(f"   - {NUM_EMPLOYEES} employees")


async def create_clients(session: AsyncSession, org_id: int):
    """Crée les clients."""
    print(f"\n🏢 Création de {NUM_CLIENTS} clients...")
    
    clients = []
    used_names = set()
    
    for i in range(NUM_CLIENTS):
        # Générer un nom de société italien
        company_name = fake.company()
        
        # Éviter les doublons
        counter = 1
        while company_name in used_names:
            company_name = f"{fake.company()} {counter}"
            counter += 1
        used_names.add(company_name)
        
        # Email basé sur le nom de la société
        email_domain = company_name.lower().replace(" ", "").replace("'", "").replace("-", "").replace(".", "")[:20]
        email = f"info@{email_domain}.it"
        
        client = Client(
            client_name=company_name,
            company_name=company_name,
            email=email,
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
            default_billing_rate=Decimal(str(random.randint(50, 150))),
            client_status="active"
        )
        clients.append(client)
    
    session.add_all(clients)
    await session.commit()
    print(f"✅ {len(clients)} clients créés")


async def create_projects(session: AsyncSession, org_id: int):
    """Crée les projets."""
    print(f"\n📁 Création de {NUM_PROJECTS} projets...")
    
    # Récupérer les clients
    result = await session.execute(select(Client))
    clients = list(result.scalars().all())
    
    # Récupérer les managers
    result = await session.execute(
        select(Employee)
        .where(Employee.role.in_(["manager", "admin"]))
        .where(Employee.org_id == org_id)
    )
    managers = list(result.scalars().all())
    
    projects = []
    project_codes = set()
    
    for i in range(NUM_PROJECTS):
        client = random.choice(clients)
        manager = random.choice(managers)
        
        start_date = datetime.utcnow() - timedelta(days=random.randint(0, 365))
        
        # Générer un code projet unique
        project_code = f"PRJ-{i+1:04d}"
        while project_code in project_codes:
            project_code = f"PRJ-{random.randint(1000, 9999)}"
        project_codes.add(project_code)
        
        status = random.choice(["active", "active", "active", "inactive"])  # 75% actifs
        
        project = Project(
            project_name=generate_project_name(),
            project_code=project_code,
            client_id=client.client_id,
            manager_id=manager.employee_id,
            start_date=start_date.date(),
            billing_rate=Decimal(str(random.randint(50, 150))),
            status=status
        )
        projects.append(project)
        
        if (i + 1) % 100 == 0:
            print(f"   {i + 1}/{NUM_PROJECTS} projets créés...")
    
    session.add_all(projects)
    await session.commit()
    print(f"✅ {len(projects)} projets créés")


async def assign_employees_to_projects(session: AsyncSession, org_id: int):
    """Assigne les employés aux projets."""
    print(f"\n👷 Assignment des employés aux projets...")
    
    # Récupérer tous les projets actifs
    result = await session.execute(
        select(Project)
        .where(Project.status == "active")
    )
    projects = list(result.scalars().all())
    
    # Récupérer tous les employés (sauf finance)
    result = await session.execute(
        select(Employee)
        .where(Employee.role != "finance")
        .where(Employee.org_id == org_id)
    )
    employees = list(result.scalars().all())
    
    assignments = []
    for project in projects:
        # Assigner 2-8 employés par projet
        num_members = random.randint(2, min(8, len(employees)))
        project_employees = random.sample(employees, num_members)
        
        for emp in project_employees:
            assignment = ProjectTeamMember(
                project_id=project.project_id,
                employee_id=emp.employee_id
            )
            assignments.append(assignment)
    
    session.add_all(assignments)
    await session.commit()
    print(f"✅ {len(assignments)} assignments créés")


async def create_timesheet_entries(session: AsyncSession, org_id: int):
    """Crée les pointages sur 12 mois."""
    print(f"\n⏱️  Création des pointages sur {MONTHS_BACK} mois...")
    
    # Récupérer tous les employés
    result = await session.execute(
        select(Employee)
        .where(Employee.role.in_(["employee", "manager", "admin"]))
        .where(Employee.org_id == org_id)
    )
    employees = list(result.scalars().all())
    
    # Récupérer les assignments
    result = await session.execute(select(ProjectTeamMember))
    assignments_list = list(result.scalars().all())
    
    # Grouper par employé
    emp_projects = {}
    for assignment in assignments_list:
        if assignment.employee_id not in emp_projects:
            emp_projects[assignment.employee_id] = []
        emp_projects[assignment.employee_id].append(assignment.project_id)
    
    entries = []
    start_date = datetime.utcnow() - timedelta(days=MONTHS_BACK * 30)
    end_date = datetime.utcnow()
    
    total_days = (end_date - start_date).days
    entry_count = 0
    
    for emp in employees:
        if emp.employee_id not in emp_projects:
            continue
        
        projects = emp_projects[emp.employee_id]
        current_date = start_date
        
        while current_date <= end_date:
            # Sauter les week-ends
            if current_date.weekday() < 5:  # Lundi = 0, Vendredi = 4
                # 90% de chance de pointer un jour donné
                if random.random() < 0.9:
                    # 1-3 projets par jour
                    num_projects = min(random.randint(1, 3), len(projects))
                    day_projects = random.sample(projects, num_projects)
                    
                    for project_id in day_projects:
                        hours = random.choice([4, 6, 7, 7.5, 8])  # Heures réalistes
                        entry_type = random.choices(
                            ["normal", "overtime", "travel", "night"],
                            weights=[85, 10, 3, 2]
                        )[0]
                        
                        # Statut basé sur l'ancienneté
                        days_ago = (end_date - current_date).days
                        if days_ago > 60:
                            status = random.choices(
                                ["approved", "rejected"],
                                weights=[95, 5]
                            )[0]
                        elif days_ago > 30:
                            status = random.choices(
                                ["approved", "submitted", "rejected"],
                                weights=[80, 15, 5]
                            )[0]
                        elif days_ago > 7:
                            status = random.choices(
                                ["submitted", "approved", "draft"],
                                weights=[60, 30, 10]
                            )[0]
                        else:
                            status = random.choices(
                                ["draft", "submitted"],
                                weights=[70, 30]
                            )[0]
                        
                        entry = TimesheetEntry(
                            employee_id=emp.employee_id,
                            project_id=project_id,
                            work_date=current_date.date(),
                            hours_worked=Decimal(str(hours)),
                            entry_type=entry_type,
                            description=f"Lavoro su {generate_project_name()}",
                            billable_flag=random.choice([True, True, True, False]),
                            status=status
                        )
                        entries.append(entry)
                        entry_count += 1
                        
                        # Commit par batch de 1000
                        if len(entries) >= 1000:
                            session.add_all(entries)
                            await session.commit()
                            print(f"   {entry_count} pointages créés...")
                            entries.clear()
            
            current_date += timedelta(days=1)
    
    # Commit final
    if entries:
        session.add_all(entries)
        await session.commit()
    
    print(f"✅ {entry_count} pointages créés")


async def create_absences(session: AsyncSession, org_id: int):
    """Crée les absences (congés, maladie, etc.)."""
    print(f"\n🏖️  Création des absences...")
    
    # Récupérer tous les employés
    result = await session.execute(
        select(Employee)
        .where(Employee.org_id == org_id)
    )
    employees = list(result.scalars().all())
    
    absences = []
    start_date = datetime.utcnow() - timedelta(days=MONTHS_BACK * 30)
    end_date = datetime.utcnow()
    
    for emp in employees:
        # 3-8 absences par employé sur 12 mois
        num_absences = random.randint(3, 8)
        
        for _ in range(num_absences):
            # Date aléatoire
            days_offset = random.randint(0, (end_date - start_date).days)
            absence_start = start_date + timedelta(days=days_offset)
            
            # Durée: 1-10 jours
            duration = random.randint(1, 10)
            absence_end = absence_start + timedelta(days=duration - 1)
            
            # Type d'absence
            absence_type = random.choices(
                ABSENCE_TYPES,
                weights=[60, 30, 10]  # CP plus fréquents
            )[0]
            
            # Statut basé sur l'ancienneté
            days_ago = (end_date - absence_start).days
            if days_ago > 30:
                status = random.choices(
                    ["approved", "rejected"],
                    weights=[90, 10]
                )[0]
            elif days_ago > 7:
                status = random.choices(
                    ["approved", "pending"],
                    weights=[70, 30]
                )[0]
            else:
                status = "pending"
            
            absence = Absence(
                employee_id=emp.employee_id,
                absence_type=absence_type,
                start_date=absence_start.date(),
                end_date=absence_end.date(),
                status=status,
                notes=f"Assenza di tipo {absence_type}"
            )
            absences.append(absence)
    
    session.add_all(absences)
    await session.commit()
    print(f"✅ {len(absences)} absences créées")


async def main():
    """Fonction principale."""
    print("=" * 60)
    print("🚀 SEED LOAD TEST - TimesheetPro Italia")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Employés: {NUM_EMPLOYEES}")
    print(f"  - Managers: {NUM_MANAGERS}")
    print(f"  - Admins: {NUM_ADMINS}")
    print(f"  - Finance: {NUM_FINANCE}")
    print(f"  - Clients: {NUM_CLIENTS}")
    print(f"  - Projets: {NUM_PROJECTS}")
    print(f"  - Période: {MONTHS_BACK} mois")
    print(f"  - Locale: Italienne (it_IT)")
    print("=" * 60)
    
    session_factory = _get_session_factory()
    async with session_factory() as session:
        # 1. Nettoyer la base
        await clear_database(session)
        
        # 2. Créer/récupérer l'organisation
        org = await create_organization(session)
        
        # 3. Créer les employés
        await create_employees(session, org.org_id)
        
        # 4. Créer les clients
        await create_clients(session, org.org_id)
        
        # 5. Créer les projets
        await create_projects(session, org.org_id)
        
        # 6. Assigner les employés aux projets
        await assign_employees_to_projects(session, org.org_id)
        
        # 7. Créer les pointages
        await create_timesheet_entries(session, org.org_id)
        
        # 8. Créer les absences
        await create_absences(session, org.org_id)
    
    print("\n" + "=" * 60)
    print("✅ SEED TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)
    print("\n📊 Résumé:")
    print(f"  - {NUM_EMPLOYEES + NUM_MANAGERS + NUM_ADMINS + NUM_FINANCE} utilisateurs")
    print(f"  - {NUM_CLIENTS} clients")
    print(f"  - {NUM_PROJECTS} projets")
    print(f"  - ~{NUM_EMPLOYEES * 20 * MONTHS_BACK} pointages estimés")
    print(f"  - ~{(NUM_EMPLOYEES + NUM_MANAGERS + NUM_ADMINS + NUM_FINANCE) * 5} absences estimées")
    print("\n🔐 Credentials:")
    print("  Email: [nome].[cognome]@[ruolo].test.it")
    print("  Password: password123")
    print("\n💡 Exempi:")
    print("  - Admin: mario.rossi@admin.test.it")
    print("  - Manager: giulia.bianchi@manager.test.it")
    print("  - Finance: luca.verdi@finance.test.it")
    print("  - Employee: anna.ferrari@emp0.test.it")
    print("\n🇮🇹 Dati generati con locale italiana (nomi, indirizzi, telefoni, aziende)")


if __name__ == "__main__":
    asyncio.run(main())
