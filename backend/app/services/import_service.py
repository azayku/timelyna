"""Service d'import CSV pour utilisateurs et projets."""
import csv
import io
import logging
import secrets
from datetime import date, datetime
from typing import Any

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.employee import Employee
from app.models.project import Project

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def parse_csv(content: bytes, expected_columns: list[str]) -> tuple[list[dict], list[str]]:
    """Parse le contenu CSV et retourne (rows, errors)."""
    errors = []
    rows = []

    try:
        text = content.decode("utf-8-sig")  # gère le BOM UTF-8
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception:
            return [], ["Encodage de fichier non supporté. Utilisez UTF-8."]

    try:
        reader = csv.DictReader(io.StringIO(text))
    except Exception as e:
        return [], [f"Erreur de parsing CSV: {str(e)}"]

    # Vérifier les colonnes
    if reader.fieldnames is None:
        return [], ["Fichier CSV vide ou invalide"]

    missing = [col for col in expected_columns if col not in reader.fieldnames]
    if missing:
        return [], [f"Colonnes manquantes : {', '.join(missing)}"]

    for i, row in enumerate(reader, start=2):
        stripped = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        rows.append({"_line": i, **stripped})

    return rows, errors


class ImportService:
    """Service gérant l'import de données CSV."""

    def __init__(self, db: AsyncSession, org_id: int = 1):
        self.db = db
        self.org_id = org_id

    async def import_employees_csv(self, content: bytes) -> dict:
        """
        Import CSV d'employés.
        Colonnes attendues: email, first_name, last_name
        Colonnes optionnelles: role, phone, department, hire_date
        """
        expected = ["email", "first_name", "last_name"]
        rows, parse_errors = parse_csv(content, expected)
        if parse_errors:
            return {"success": 0, "errors": parse_errors, "skipped": 0}

        created = 0
        skipped = 0
        errors = []
        valid_roles = ["employee", "manager", "admin", "finance"]

        for row in rows:
            line = row.get("_line", "?")
            email = row.get("email", "").lower().strip()
            if not email:
                errors.append(f"Ligne {line}: email manquant")
                continue

            # Validation basique email
            if "@" not in email or "." not in email.split("@")[1]:
                errors.append(f"Ligne {line}: email invalide '{email}'")
                continue

            first_name = row.get("first_name", "").strip()
            last_name = row.get("last_name", "").strip()
            if not first_name or not last_name:
                errors.append(f"Ligne {line}: nom et prénom requis")
                continue

            role = row.get("role", "employee").lower().strip()
            if role not in valid_roles:
                role = "employee"

            # Vérifier si l'email existe déjà
            existing = await self.db.execute(select(Employee).where(Employee.email == email))
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Générer username et mot de passe temporaire
            username = email.split("@")[0]
            # S'assurer que le username est unique
            username_exists = await self.db.execute(
                select(Employee).where(Employee.username == username)
            )
            if username_exists.scalar_one_or_none():
                username = f"{username}_{secrets.token_hex(3)}"

            temp_password = secrets.token_urlsafe(12)
            hashed = pwd_context.hash(temp_password)

            # Parser hire_date si présent
            hire_date_val = None
            hire_date_str = row.get("hire_date", "").strip()
            if hire_date_str:
                try:
                    hire_date_val = date.fromisoformat(hire_date_str)
                except ValueError:
                    errors.append(
                        f"Ligne {line}: date d'embauche invalide '{hire_date_str}' (format: YYYY-MM-DD)"
                    )
                    continue

            employee = Employee(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                org_id=self.org_id,
                password_hash=hashed,
                username=username,
                must_change_password=True,
                employment_status="active",
                phone=row.get("phone", "").strip() or None,
                department=row.get("department", "").strip() or None,
                hire_date=hire_date_val,
            )
            self.db.add(employee)
            created += 1

            logger.info(f"Employee créé: {email} (username: {username}, password: {temp_password})")

        await self.db.commit()
        return {"success": created, "skipped": skipped, "errors": errors}

    async def import_projects_csv(self, content: bytes) -> dict:
        """
        Import CSV de projets.
        Colonnes attendues: project_name, project_code, client_name (ou client_id)
        Colonnes optionnelles: description, start_date, end_date, budget_hours, manager_email
        """
        expected = ["project_name", "project_code"]
        rows, parse_errors = parse_csv(content, expected)
        if parse_errors:
            return {"success": 0, "errors": parse_errors, "skipped": 0}

        created = 0
        skipped = 0
        errors = []

        # Cache pour les clients et managers
        clients_cache: dict[str, Client] = {}
        managers_cache: dict[str, Employee] = {}

        for row in rows:
            line = row.get("_line", "?")
            project_name = row.get("project_name", "").strip()
            project_code = row.get("project_code", "").strip()

            if not project_name:
                errors.append(f"Ligne {line}: nom de projet manquant")
                continue

            if not project_code:
                errors.append(f"Ligne {line}: code projet manquant")
                continue

            # Vérifier doublons par project_code
            existing = await self.db.execute(
                select(Project).where(Project.project_code == project_code)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Résoudre le client
            client_id_val = None
            client_name = row.get("client_name", "").strip()
            client_id_str = row.get("client_id", "").strip()

            if client_id_str:
                try:
                    client_id_val = int(client_id_str)
                    # Vérifier existence
                    client_check = await self.db.execute(
                        select(Client).where(Client.client_id == client_id_val)
                    )
                    if not client_check.scalar_one_or_none():
                        errors.append(f"Ligne {line}: client_id {client_id_val} introuvable")
                        continue
                except ValueError:
                    errors.append(f"Ligne {line}: client_id invalide '{client_id_str}'")
                    continue
            elif client_name:
                # Chercher par nom (cache)
                if client_name not in clients_cache:
                    client_result = await self.db.execute(
                        select(Client).where(Client.client_name == client_name)
                    )
                    client = client_result.scalar_one_or_none()
                    if client:
                        clients_cache[client_name] = client
                    else:
                        errors.append(f"Ligne {line}: client '{client_name}' introuvable")
                        continue
                client_id_val = clients_cache[client_name].client_id
            else:
                errors.append(f"Ligne {line}: client_name ou client_id requis")
                continue

            # Résoudre le manager
            manager_id_val = None
            manager_email = row.get("manager_email", "").strip()
            if manager_email:
                if manager_email not in managers_cache:
                    mgr_result = await self.db.execute(
                        select(Employee).where(Employee.email == manager_email)
                    )
                    manager = mgr_result.scalar_one_or_none()
                    if manager:
                        managers_cache[manager_email] = manager
                    else:
                        errors.append(f"Ligne {line}: manager '{manager_email}' introuvable")
                        continue
                manager_id_val = managers_cache[manager_email].employee_id
            else:
                # Manager par défaut : premier admin de l'org
                default_mgr = await self.db.execute(
                    select(Employee)
                    .where(Employee.org_id == self.org_id, Employee.role == "admin")
                    .limit(1)
                )
                manager = default_mgr.scalar_one_or_none()
                if not manager:
                    errors.append(f"Ligne {line}: aucun manager trouvé (précisez manager_email)")
                    continue
                manager_id_val = manager.employee_id

            # Parser les dates
            start_date_val = None
            start_str = row.get("start_date", "").strip()
            if start_str:
                try:
                    start_date_val = date.fromisoformat(start_str)
                except ValueError:
                    errors.append(
                        f"Ligne {line}: start_date invalide '{start_str}' (format: YYYY-MM-DD)"
                    )
                    continue
            else:
                start_date_val = date.today()

            end_date_val = None
            end_str = row.get("end_date", "").strip()
            if end_str:
                try:
                    end_date_val = date.fromisoformat(end_str)
                except ValueError:
                    errors.append(
                        f"Ligne {line}: end_date invalide '{end_str}' (format: YYYY-MM-DD)"
                    )
                    continue

            # Parser budget_hours
            budget_hours_val = None
            budget_str = row.get("budget_hours", "").strip()
            if budget_str:
                try:
                    budget_hours_val = float(budget_str)
                except ValueError:
                    errors.append(f"Ligne {line}: budget_hours invalide '{budget_str}'")
                    continue

            # Billing rate par défaut (peut être overridé si fourni)
            billing_rate_val = 0.0
            billing_str = row.get("billing_rate", "").strip()
            if billing_str:
                try:
                    billing_rate_val = float(billing_str)
                except ValueError:
                    errors.append(f"Ligne {line}: billing_rate invalide '{billing_str}'")
                    continue

            project = Project(
                project_name=project_name,
                project_code=project_code,
                client_id=client_id_val,
                manager_id=manager_id_val,
                description=row.get("description", "").strip() or None,
                status="active",
                start_date=start_date_val,
                end_date=end_date_val,
                budget_hours=budget_hours_val,
                billing_rate=billing_rate_val,
            )
            self.db.add(project)
            created += 1

        await self.db.commit()
        return {"success": created, "skipped": skipped, "errors": errors}
