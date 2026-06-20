"""
Génère un fichier SQL avec des INSERT directs pour PostgreSQL.
Basé sur seed_big.py — 500 employés, 300 clients, 1000 projets, etc.

Run: python backend/seed_sql.py > backend/seed_data.sql
"""
from __future__ import annotations

import random
import sys
import os
from datetime import date, timedelta, datetime
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import bcrypt
from faker import Faker

fake = Faker("fr_FR")
Faker.seed(42)
random.seed(42)

TASK_TYPES = ["dev", "design", "testing", "meeting", "doc", "other"]
DEPARTMENTS = ["Engineering", "Design", "QA", "Product", "DevOps", "Data", "Support", "Finance"]


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=6)).decode()


def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def esc(s) -> str:
    """Escape single quotes for SQL."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def sql_date(d) -> str:
    if d is None:
        return "NULL"
    return f"'{d}'"


def sql_bool(b: bool) -> str:
    return "TRUE" if b else "FALSE"


lines = []


def emit(sql: str):
    lines.append(sql)


def main():
    emit("-- ============================================================")
    emit("-- Timelyna — Seed Data (généré par seed_sql.py)")
    emit("-- ============================================================")
    emit("BEGIN;")
    emit("")

    # ── Org Settings ──────────────────────────────────────────────────────
    emit("-- Org Settings")
    emit("INSERT INTO org_settings (org_id, org_name, standard_hours_per_day, max_hours_per_day, overtime_rate_multiplier, travel_rate_multiplier, default_currency)")
    emit("VALUES (1, 'Timelyna Demo', 8.00, 24.00, 1.25, 0.50, 'EUR')")
    emit("ON CONFLICT (org_id) DO NOTHING;")
    emit("")

    # ── Admins ────────────────────────────────────────────────────────────
    emit("-- Admins (2)")
    admin_pw = hash_pw("Admin1234!")
    admins = []
    for i in range(1, 3):
        email = f"admin{i}@timelyna.com"
        fn = fake.first_name()
        ln = fake.last_name()
        username = f"admin{i:03d}"
        emit(f"INSERT INTO employees (email, first_name, last_name, password_hash, role, employment_status, department, org_id, username, must_change_password)")
        emit(f"VALUES ({esc(email)}, {esc(fn)}, {esc(ln)}, {esc(admin_pw)}, 'admin', 'active', 'Management', 1, {esc(username)}, FALSE)")
        emit(f"ON CONFLICT (email) DO NOTHING;")
        admins.append({"email": email, "fn": fn, "ln": ln})
    emit("")

    # ── Finance users ─────────────────────────────────────────────────────
    emit("-- Finance users (2)")
    finance_pw = hash_pw("Finance1234!")
    for i in range(1, 3):
        email = f"finance{i}@timelyna.com"
        fn = fake.first_name()
        ln = fake.last_name()
        username = f"fin{i:03d}"
        emit(f"INSERT INTO employees (email, first_name, last_name, password_hash, role, employment_status, department, org_id, username, must_change_password)")
        emit(f"VALUES ({esc(email)}, {esc(fn)}, {esc(ln)}, {esc(finance_pw)}, 'finance', 'active', 'Finance', 1, {esc(username)}, FALSE)")
        emit(f"ON CONFLICT (email) DO NOTHING;")
    emit("")

    # ── Managers (20) ─────────────────────────────────────────────────────
    emit("-- Managers (20)")
    mgr_pw = hash_pw("Manager1234!")
    manager_emails = []
    for i in range(1, 21):
        email = fake.unique.email()
        fn = fake.first_name()
        ln = fake.last_name()
        dept = random.choice(DEPARTMENTS)
        cost = round(random.uniform(40, 80), 2)
        username = f"mgr{i:03d}"
        emit(f"INSERT INTO employees (email, first_name, last_name, password_hash, role, employment_status, department, hourly_cost, org_id, username, must_change_password)")
        emit(f"VALUES ({esc(email)}, {esc(fn)}, {esc(ln)}, {esc(mgr_pw)}, 'manager', 'active', {esc(dept)}, {cost}, 1, {esc(username)}, FALSE)")
        emit(f"ON CONFLICT (email) DO NOTHING;")
        manager_emails.append(email)
    emit("")

    # ── Employees (500) ───────────────────────────────────────────────────
    emit("-- Employees (500)")
    emp_pw = hash_pw("Employee1234!")
    employee_emails = []
    for i in range(1, 501):
        email = fake.unique.email()
        fn = fake.first_name()
        ln = fake.last_name()
        dept = random.choice(DEPARTMENTS)
        cost = round(random.uniform(25, 60), 2)
        status = random.choices(["active", "inactive"], weights=[95, 5])[0]
        hire = fake.date_between(start_date="-5y", end_date="today")
        username = f"emp{i:04d}"
        emit(f"INSERT INTO employees (email, first_name, last_name, password_hash, role, employment_status, department, hourly_cost, hire_date, org_id, username, must_change_password)")
        emit(f"VALUES ({esc(email)}, {esc(fn)}, {esc(ln)}, {esc(emp_pw)}, 'employee', {esc(status)}, {esc(dept)}, {cost}, {sql_date(hire)}, 1, {esc(username)}, FALSE)")
        emit(f"ON CONFLICT (email) DO NOTHING;")
        employee_emails.append(email)
        if i % 100 == 0:
            sys.stderr.write(f"  employees: {i}/500\n")
    emit("")

    # ── Assign manager_id to employees via UPDATE ─────────────────────────
    emit("-- Assign manager_id to employees")
    emit("""DO $$
DECLARE
  mgr_ids BIGINT[];
  emp_rec RECORD;
BEGIN
  SELECT ARRAY(SELECT employee_id FROM employees WHERE role = 'manager' ORDER BY employee_id) INTO mgr_ids;
  FOR emp_rec IN SELECT employee_id FROM employees WHERE role = 'employee' LOOP
    UPDATE employees
    SET manager_id = mgr_ids[1 + (emp_rec.employee_id % array_length(mgr_ids, 1))]
    WHERE employee_id = emp_rec.employee_id;
  END LOOP;
END $$;
""")

    # ── Clients (300) ─────────────────────────────────────────────────────
    emit("-- Clients (300)")
    client_names = []
    for i in range(1, 301):
        name = fake.company()
        company = fake.company()
        email = fake.unique.company_email()
        phone = fake.phone_number()[:20]
        addr = fake.address().replace("\n", ", ")[:200]
        rate = round(random.uniform(80, 250), 2)
        currency = random.choices(["EUR", "USD", "GBP"], weights=[70, 20, 10])[0]
        status = random.choices(["active", "inactive"], weights=[90, 10])[0]
        emit(f"INSERT INTO clients (client_name, company_name, email, phone, address, default_billing_rate, currency, client_status)")
        emit(f"VALUES ({esc(name)}, {esc(company)}, {esc(email)}, {esc(phone)}, {esc(addr)}, {rate}, {esc(currency)}, {esc(status)})")
        emit(f"ON CONFLICT DO NOTHING;")
        client_names.append({"name": name, "status": status})
        if i % 100 == 0:
            sys.stderr.write(f"  clients: {i}/300\n")
    emit("")

    # ── Skill Rates ───────────────────────────────────────────────────────
    emit("-- Skill Rates")
    skills = [
        ("Développement Backend", 120.00),
        ("Développement Frontend", 110.00),
        ("DevOps / Infrastructure", 130.00),
        ("Data Science", 140.00),
        ("Design UX/UI", 100.00),
        ("Chef de projet", 115.00),
        ("QA / Tests", 90.00),
        ("Consulting", 150.00),
    ]
    for skill_name, rate in skills:
        emit(f"INSERT INTO skill_rates (org_id, skill_name, billing_rate)")
        emit(f"VALUES (1, {esc(skill_name)}, {rate})")
        emit(f"ON CONFLICT (org_id, skill_name) DO NOTHING;")
    emit("")

    # ── Projects (1000) ───────────────────────────────────────────────────
    emit("-- Projects (1000)")
    used_codes: set[str] = set()
    for i in range(1, 1001):
        while True:
            code = f"{fake.lexify('?????').upper()}-{random.randint(1000, 9999)}"
            if code not in used_codes:
                used_codes.add(code)
                break
        pname = f"{fake.bs().title()} {fake.word().title()}"[:255]
        desc = fake.sentence(nb_words=10)
        status = random.choices(["active", "active", "active", "paused", "completed"], weights=[50, 20, 15, 10, 5])[0]
        rate = round(random.uniform(80, 300), 2)
        start = fake.date_between(start_date="-2y", end_date="-1m")
        budget_h = round(random.uniform(50, 2000), 0)
        budget_a = round(random.uniform(5000, 500000), 2)
        # client_id and manager_id resolved dynamically
        emit(f"""INSERT INTO projects (client_id, project_name, project_code, description, status, billing_rate, manager_id, start_date, budget_hours, budget_amount, team_members)
SELECT
  (SELECT client_id FROM clients WHERE client_status = 'active' ORDER BY RANDOM() LIMIT 1),
  {esc(pname)},
  {esc(code)},
  {esc(desc)},
  {esc(status)},
  {rate},
  (SELECT employee_id FROM employees WHERE role = 'manager' ORDER BY RANDOM() LIMIT 1),
  {sql_date(start)},
  {budget_h},
  {budget_a},
  '[]'::json
ON CONFLICT (project_code) DO NOTHING;""")
        if i % 200 == 0:
            sys.stderr.write(f"  projects: {i}/1000\n")
    emit("")

    # ── Assign team_members to projects ───────────────────────────────────
    emit("-- Assign team_members (3-15 employees per project)")
    emit("""DO $$
DECLARE
  proj_rec RECORD;
  emp_ids BIGINT[];
  team_size INT;
  team_sample BIGINT[];
  i INT;
BEGIN
  SELECT ARRAY(SELECT employee_id FROM employees WHERE role = 'employee' AND employment_status = 'active') INTO emp_ids;
  FOR proj_rec IN SELECT project_id FROM projects LOOP
    team_size := 3 + (proj_rec.project_id % 13);
    team_sample := ARRAY[]::BIGINT[];
    FOR i IN 1..team_size LOOP
      team_sample := array_append(team_sample, emp_ids[1 + ((proj_rec.project_id * i) % array_length(emp_ids, 1))]);
    END LOOP;
    UPDATE projects SET team_members = to_json(team_sample) WHERE project_id = proj_rec.project_id;
  END LOOP;
END $$;
""")

    # ── Timesheet Entries + Approvals ─────────────────────────────────────
    emit("-- Timesheet entries + approvals (last 12 weeks, sample of 100 employees)")
    emit("""DO $$
DECLARE
  v_emp_id BIGINT;
  v_mgr_id BIGINT;
  v_proj_id BIGINT;
  v_week_offset INT;
  v_day_offset INT;
  v_entry_date DATE;
  v_week_monday DATE;
  v_entry_status VARCHAR(50);
  v_hours_val NUMERIC(5,2);
  v_task_types TEXT[] := ARRAY['dev','design','testing','meeting','doc','other'];
  v_descriptions TEXT[] := ARRAY[
    'Developpement de la fonctionnalite principale',
    'Revue de code et corrections',
    'Reunion de suivi projet',
    'Tests unitaires et integration',
    'Documentation technique',
    'Correction de bugs critiques',
    'Mise en place CI/CD',
    'Analyse des besoins client',
    'Deploiement en production',
    'Formation equipe'
  ];
  v_hours_options NUMERIC[] := ARRAY[4.0, 6.0, 7.0, 7.5, 8.0, 8.5];
BEGIN
  FOR v_emp_id, v_mgr_id IN
    SELECT e.employee_id, e.manager_id
    FROM employees e
    WHERE e.role = 'employee' AND e.employment_status = 'active'
    ORDER BY e.employee_id
    LIMIT 100
  LOOP
    -- Get a project for this employee
    SELECT p.project_id INTO v_proj_id
    FROM projects p
    WHERE p.status = 'active'
    ORDER BY RANDOM()
    LIMIT 1;

    IF v_proj_id IS NULL THEN CONTINUE; END IF;

    FOR v_week_offset IN 1..12 LOOP
      v_week_monday := date_trunc('week', CURRENT_DATE)::date - (v_week_offset * 7);

      IF random() < 0.2 THEN CONTINUE; END IF;

      FOR v_day_offset IN 0..4 LOOP
        IF random() < 0.2 THEN CONTINUE; END IF;

        v_entry_date := v_week_monday + v_day_offset;
        IF v_entry_date > CURRENT_DATE THEN CONTINUE; END IF;

        v_hours_val := v_hours_options[1 + floor(random() * 6)::int];

        IF v_week_offset = 1 THEN
          v_entry_status := 'submitted';
        ELSE
          v_entry_status := CASE WHEN random() < 0.85 THEN 'approved' ELSE 'rejected' END;
        END IF;

        INSERT INTO timesheet_entries
          (employee_id, project_id, work_date, hours_worked, description, task_type, billable_flag, status, submitted_at, approved_at)
        VALUES (
          v_emp_id,
          v_proj_id,
          v_entry_date,
          v_hours_val,
          v_descriptions[1 + floor(random() * 10)::int],
          v_task_types[1 + floor(random() * 6)::int],
          random() > 0.1,
          v_entry_status,
          CASE WHEN v_entry_status != 'draft' THEN (v_week_monday + 5)::timestamp ELSE NULL END,
          CASE WHEN v_entry_status = 'approved' THEN (v_week_monday + 6)::timestamp ELSE NULL END
        )
        ON CONFLICT (employee_id, project_id, work_date, entry_type) DO NOTHING;
      END LOOP;

      INSERT INTO approvals (employee_id, manager_id, week_start, status, decided_at)
      VALUES (
        v_emp_id,
        COALESCE(v_mgr_id, (SELECT employee_id FROM employees WHERE role = 'manager' LIMIT 1)),
        v_week_monday,
        CASE
          WHEN v_week_offset = 1 THEN 'pending'
          WHEN random() < 0.85 THEN 'approved'
          ELSE 'rejected'
        END,
        CASE WHEN v_week_offset > 1 THEN (v_week_monday + 6)::timestamp ELSE NULL END
      )
      ON CONFLICT (employee_id, week_start) DO NOTHING;

    END LOOP;
  END LOOP;
END $$;
""")

    # ── Invoices (50 samples) ─────────────────────────────────────────────
    emit("-- Invoices (50 samples)")
    emit("""DO $$
DECLARE
  i INT;
  inv_client_id BIGINT;
  inv_status VARCHAR(50);
  inv_statuses TEXT[] := ARRAY['draft','sent','paid','overdue'];
  inv_amount NUMERIC(12,2);
  inv_period VARCHAR(10);
  inv_year INT;
  inv_month INT;
BEGIN
  FOR i IN 1..50 LOOP
    SELECT client_id INTO inv_client_id FROM clients WHERE client_status = 'active' ORDER BY RANDOM() LIMIT 1;
    inv_status := inv_statuses[1 + floor(random() * 4)::int];
    inv_amount := round((random() * 50000 + 1000)::numeric, 2);
    inv_year := 2024 + floor(random() * 2)::int;
    inv_month := 1 + floor(random() * 12)::int;
    inv_period := inv_year::text || '-' || lpad(inv_month::text, 2, '0');

    INSERT INTO invoices (client_id, invoice_number, period, total_hours, total_amount, tax_rate, currency, status, created_by)
    VALUES (
      inv_client_id,
      'FAC-' || inv_year::text || '-' || lpad(i::text, 4, '0'),
      inv_period,
      round((random() * 200 + 10)::numeric, 2),
      inv_amount,
      20.00,
      'EUR',
      inv_status,
      (SELECT employee_id FROM employees WHERE role IN ('admin','finance') ORDER BY RANDOM() LIMIT 1)
    )
    ON CONFLICT (invoice_number) DO NOTHING;
  END LOOP;
END $$;
""")

    emit("COMMIT;")
    emit("")
    emit("-- ============================================================")
    emit("-- Comptes de connexion :")
    emit("--   admin1@timelyna.com / Admin1234!")
    emit("--   admin2@timelyna.com / Admin1234!")
    emit("--   finance1@timelyna.com / Finance1234!")
    emit("--   manager (20 comptes) / Manager1234!")
    emit("--   employee (500 comptes) / Employee1234!")
    emit("-- ============================================================")

    print("\n".join(lines))
    sys.stderr.write("\n✓ SQL généré avec succès\n")


if __name__ == "__main__":
    main()
