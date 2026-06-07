"""ReportingRepository — raw SQL aggregate queries for reporting."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ReportingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_personal_stats(
        self, employee_id: int, start_date: date, end_date: date
    ) -> dict:
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(SUM(hours_worked), 0) AS total_hours,
                    COALESCE(SUM(CASE WHEN billable_flag THEN hours_worked ELSE 0 END), 0) AS billable_hours,
                    COUNT(DISTINCT work_date) AS days_worked,
                    COUNT(CASE WHEN status IN ('approved', 'invoiced') THEN 1 END) AS approved_count,
                    COUNT(CASE WHEN status = 'submitted' THEN 1 END) AS submitted_count
                FROM timesheet_entries
                WHERE employee_id = :employee_id
                  AND work_date BETWEEN :start_date AND :end_date
                  AND deleted_at IS NULL
            """),
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        row = result.mappings().one()
        return {
            "total_hours": float(row["total_hours"] or 0),
            "billable_hours": float(row["billable_hours"] or 0),
            "days_worked": int(row["days_worked"] or 0),
            "approved_count": int(row["approved_count"] or 0),
            "submitted_count": int(row["submitted_count"] or 0),
        }

    async def get_project_breakdown(
        self, employee_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    te.project_id,
                    p.project_name,
                    COALESCE(SUM(te.hours_worked), 0) AS hours
                FROM timesheet_entries te
                JOIN projects p ON te.project_id = p.project_id
                WHERE te.employee_id = :employee_id
                  AND te.work_date BETWEEN :start_date AND :end_date
                  AND te.deleted_at IS NULL
                GROUP BY te.project_id, p.project_name
                ORDER BY hours DESC
            """),
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        return [
            {"project_id": row["project_id"], "project_name": row["project_name"], "hours": float(row["hours"])}
            for row in result.mappings().all()
        ]

    async def get_task_type_breakdown(
        self, employee_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    task_type,
                    COALESCE(SUM(hours_worked), 0) AS hours
                FROM timesheet_entries
                WHERE employee_id = :employee_id
                  AND work_date BETWEEN :start_date AND :end_date
                  AND deleted_at IS NULL
                GROUP BY task_type
                ORDER BY hours DESC
            """),
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        return [
            {"task_type": row["task_type"], "hours": float(row["hours"])}
            for row in result.mappings().all()
        ]

    async def get_weekly_trend(
        self, employee_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    TO_CHAR(DATE_TRUNC('week', work_date), 'IYYY-"W"IW') AS week,
                    COALESCE(SUM(hours_worked), 0) AS hours
                FROM timesheet_entries
                WHERE employee_id = :employee_id
                  AND work_date BETWEEN :start_date AND :end_date
                  AND deleted_at IS NULL
                GROUP BY DATE_TRUNC('week', work_date)
                ORDER BY DATE_TRUNC('week', work_date)
            """),
            {"employee_id": employee_id, "start_date": start_date, "end_date": end_date},
        )
        return [
            {"week": row["week"], "hours": float(row["hours"])}
            for row in result.mappings().all()
        ]

    async def get_team_stats(
        self, manager_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    e.employee_id,
                    e.first_name || ' ' || e.last_name AS name,
                    COALESCE(SUM(te.hours_worked), 0) AS total_hours,
                    COALESCE(SUM(CASE WHEN te.billable_flag THEN te.hours_worked ELSE 0 END), 0) AS billable_hours,
                    COUNT(CASE WHEN te.status = 'submitted' THEN 1 END) AS pending_count
                FROM employees e
                LEFT JOIN timesheet_entries te
                    ON te.employee_id = e.employee_id
                    AND te.work_date BETWEEN :start_date AND :end_date
                    AND te.deleted_at IS NULL
                WHERE e.manager_id = :manager_id
                  AND e.deleted_at IS NULL
                GROUP BY e.employee_id, e.first_name, e.last_name
                ORDER BY e.first_name, e.last_name
            """),
            {"manager_id": manager_id, "start_date": start_date, "end_date": end_date},
        )
        return [
            {
                "employee_id": row["employee_id"],
                "name": row["name"],
                "total_hours": float(row["total_hours"]),
                "billable_hours": float(row["billable_hours"]),
                "pending_count": int(row["pending_count"]),
            }
            for row in result.mappings().all()
        ]

    async def get_financial_report(
        self, start_date: date, end_date: date, client_id: Optional[int] = None
    ) -> list[dict]:
        client_filter = "AND p.client_id = :client_id" if client_id else ""
        params: dict = {"start_date": start_date, "end_date": end_date}
        if client_id:
            params["client_id"] = client_id

        result = await self.db.execute(
            text(f"""
                SELECT
                    p.project_id,
                    p.project_name,
                    c.client_name,
                    COALESCE(p.budget_hours, 0) AS budget_hours,
                    COALESCE(SUM(te.hours_worked), 0) AS actual_hours,
                    COALESCE(SUM(te.hours_worked * COALESCE(te.billing_rate, p.billing_rate)), 0) AS revenue,
                    COALESCE(SUM(te.hours_worked * COALESCE(e.hourly_cost, 0)), 0) AS internal_cost
                FROM projects p
                JOIN clients c ON p.client_id = c.client_id
                LEFT JOIN timesheet_entries te
                    ON te.project_id = p.project_id
                    AND te.status IN ('approved', 'invoiced')
                    AND te.deleted_at IS NULL
                    AND te.work_date BETWEEN :start_date AND :end_date
                LEFT JOIN employees e ON te.employee_id = e.employee_id
                WHERE p.deleted_at IS NULL
                  {client_filter}
                GROUP BY p.project_id, p.project_name, c.client_name, p.budget_hours
                ORDER BY p.project_name
            """),
            params,
        )
        rows = []
        for row in result.mappings().all():
            budget_hours = float(row["budget_hours"] or 0)
            actual_hours = float(row["actual_hours"] or 0)
            budget_warning = budget_hours > 0 and actual_hours > budget_hours * 0.8
            rows.append({
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "client_name": row["client_name"],
                "budget_hours": budget_hours,
                "actual_hours": actual_hours,
                "revenue": float(row["revenue"] or 0),
                "internal_cost": float(row["internal_cost"] or 0),
                "budget_warning": budget_warning,
            })
        return rows

    async def get_hours_report(
        self,
        date_from: date,
        date_to: date,
        employee_id: Optional[int] = None,
        project_id: Optional[int] = None,
        group_by: str = "day",
    ) -> list[dict]:
        """
        Detailed hours report with breakdown by entry_type (normal/overtime/travel/night).
        group_by: day | project | employee | entry_type
        """
        filters = ["te.deleted_at IS NULL", "te.work_date BETWEEN :date_from AND :date_to"]
        params: dict = {"date_from": date_from, "date_to": date_to}

        if employee_id:
            filters.append("te.employee_id = :employee_id")
            params["employee_id"] = employee_id
        if project_id:
            filters.append("te.project_id = :project_id")
            params["project_id"] = project_id

        where = " AND ".join(filters)

        if group_by == "day":
            select_cols = "te.work_date AS period_key"
            group_cols = "te.work_date"
            order_cols = "te.work_date DESC"
        elif group_by == "project":
            select_cols = "p.project_name AS period_key"
            group_cols = "p.project_name"
            order_cols = "p.project_name"
        elif group_by == "employee":
            select_cols = "e.first_name || ' ' || e.last_name AS period_key"
            group_cols = "e.first_name, e.last_name"
            order_cols = "e.last_name, e.first_name"
        else:  # entry_type
            select_cols = "te.entry_type AS period_key"
            group_cols = "te.entry_type"
            order_cols = "te.entry_type"

        result = await self.db.execute(
            text(f"""
                SELECT
                    {select_cols},
                    e.first_name || ' ' || e.last_name AS employee_name,
                    e.employee_id,
                    p.project_name,
                    p.project_id,
                    te.work_date,
                    te.entry_type,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'normal'   THEN te.hours_worked ELSE 0 END), 0) AS normal_hours,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'overtime' THEN te.hours_worked ELSE 0 END), 0) AS overtime_hours,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'travel'   THEN te.hours_worked ELSE 0 END), 0) AS travel_hours,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'night'    THEN te.hours_worked ELSE 0 END), 0) AS night_hours,
                    COALESCE(SUM(te.hours_worked), 0) AS total_hours
                FROM timesheet_entries te
                JOIN employees e ON te.employee_id = e.employee_id
                JOIN projects p ON te.project_id = p.project_id
                WHERE {where}
                GROUP BY {group_cols}, e.employee_id, e.first_name, e.last_name, p.project_id, p.project_name, te.work_date, te.entry_type
                ORDER BY {order_cols}
            """),
            params,
        )
        rows = []
        for row in result.mappings().all():
            rows.append({
                "period_key": str(row["period_key"]),
                "employee_id": row["employee_id"],
                "employee_name": row["employee_name"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "work_date": str(row["work_date"]),
                "entry_type": row["entry_type"],
                "normal_hours": float(row["normal_hours"]),
                "overtime_hours": float(row["overtime_hours"]),
                "travel_hours": float(row["travel_hours"]),
                "night_hours": float(row["night_hours"]),
                "total_hours": float(row["total_hours"]),
            })
        return rows

    async def get_project_profitability(self) -> list[dict]:
        """Budget hours vs actual hours + margin per project."""
        result = await self.db.execute(
            text("""
                SELECT
                    p.project_id,
                    p.project_name,
                    c.client_name,
                    COALESCE(p.budget_hours, 0) AS budget_hours,
                    COALESCE(p.budget_amount, 0) AS budget_amount,
                    COALESCE(SUM(te.hours_worked), 0) AS actual_hours,
                    COALESCE(SUM(te.hours_worked * COALESCE(te.billing_rate, p.billing_rate)), 0) AS revenue,
                    COALESCE(SUM(te.hours_worked * COALESCE(e.hourly_cost, 0)), 0) AS internal_cost
                FROM projects p
                JOIN clients c ON p.client_id = c.client_id
                LEFT JOIN timesheet_entries te
                    ON te.project_id = p.project_id
                    AND te.status IN ('approved', 'invoiced')
                    AND te.deleted_at IS NULL
                LEFT JOIN employees e ON te.employee_id = e.employee_id
                WHERE p.deleted_at IS NULL
                GROUP BY p.project_id, p.project_name, c.client_name, p.budget_hours, p.budget_amount
                ORDER BY revenue DESC
            """),
        )
        rows = []
        for row in result.mappings().all():
            budget_hours = float(row["budget_hours"] or 0)
            actual_hours = float(row["actual_hours"] or 0)
            revenue = float(row["revenue"] or 0)
            internal_cost = float(row["internal_cost"] or 0)
            margin = revenue - internal_cost
            margin_pct = round(margin / revenue * 100, 1) if revenue > 0 else 0.0
            hours_variance = budget_hours - actual_hours
            rows.append({
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "client_name": row["client_name"],
                "budget_hours": budget_hours,
                "actual_hours": actual_hours,
                "hours_variance": hours_variance,
                "revenue": revenue,
                "internal_cost": internal_cost,
                "margin": margin,
                "margin_pct": margin_pct,
            })
        return rows

    async def get_aging_report(self) -> dict:
        """Receivables aging: 0-30d, 31-60d, 61-90d, >90d based on due_date of sent invoices."""
        result = await self.db.execute(
            text("""
                SELECT
                    i.invoice_id,
                    i.invoice_number,
                    c.client_name,
                    i.total_amount,
                    i.currency,
                    i.due_date,
                    CURRENT_DATE - i.due_date AS days_overdue
                FROM invoices i
                JOIN clients c ON i.client_id = c.client_id
                WHERE i.status IN ('sent', 'overdue')
                  AND i.due_date IS NOT NULL
                  AND i.due_date < CURRENT_DATE
                ORDER BY i.due_date ASC
            """),
        )
        rows = result.mappings().all()

        buckets: dict[str, list] = {
            "0_30": [],
            "31_60": [],
            "61_90": [],
            "over_90": [],
        }
        totals: dict[str, float] = {"0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0}

        for row in rows:
            days = int(row["days_overdue"] or 0)
            amount = float(row["total_amount"] or 0)
            entry = {
                "invoice_id": row["invoice_id"],
                "invoice_number": row["invoice_number"],
                "client_name": row["client_name"],
                "total_amount": amount,
                "currency": row["currency"],
                "due_date": str(row["due_date"]),
                "days_overdue": days,
            }
            if days <= 30:
                buckets["0_30"].append(entry)
                totals["0_30"] += amount
            elif days <= 60:
                buckets["31_60"].append(entry)
                totals["31_60"] += amount
            elif days <= 90:
                buckets["61_90"].append(entry)
                totals["61_90"] += amount
            else:
                buckets["over_90"].append(entry)
                totals["over_90"] += amount

        return {
            "buckets": buckets,
            "totals": totals,
            "grand_total": sum(totals.values()),
        }

    async def get_cashflow_forecast(self, months: int = 3) -> list[dict]:
        """Cashflow forecast based on sent (unpaid) invoices grouped by expected payment month."""
        result = await self.db.execute(
            text("""
                SELECT
                    TO_CHAR(COALESCE(i.due_date, i.created_at::date + INTERVAL '30 days'), 'YYYY-MM') AS month,
                    COALESCE(SUM(i.total_amount), 0) AS expected_amount,
                    COUNT(i.invoice_id) AS invoice_count
                FROM invoices i
                WHERE i.status IN ('sent', 'overdue')
                  AND COALESCE(i.due_date, i.created_at::date + INTERVAL '30 days') <= CURRENT_DATE + (:months * INTERVAL '1 month')
                GROUP BY TO_CHAR(COALESCE(i.due_date, i.created_at::date + INTERVAL '30 days'), 'YYYY-MM')
                ORDER BY month
            """),
            {"months": months},
        )
        return [
            {
                "month": row["month"],
                "expected_amount": float(row["expected_amount"]),
                "invoice_count": int(row["invoice_count"]),
            }
            for row in result.mappings().all()
        ]

    async def get_overtime_hours(
        self, manager_id: int, start_date: date, end_date: date
    ) -> float:
        """Get total overtime hours for manager's team."""
        result = await self.db.execute(
            text("""
                SELECT COALESCE(SUM(te.hours_worked), 0) AS overtime_hours
                FROM timesheet_entries te
                JOIN employees e ON te.employee_id = e.employee_id
                WHERE e.manager_id = :manager_id
                  AND te.entry_type = 'overtime'
                  AND te.work_date BETWEEN :start_date AND :end_date
                  AND te.deleted_at IS NULL
                  AND e.deleted_at IS NULL
            """),
            {"manager_id": manager_id, "start_date": start_date, "end_date": end_date},
        )
        row = result.mappings().one()
        return float(row["overtime_hours"] or 0)

    async def get_monthly_trend(self, manager_id: int, months: int = 9) -> list[dict]:
        """Get monthly hours trend for manager's team (last N months)."""
        result = await self.db.execute(
            text("""
                SELECT
                    TO_CHAR(DATE_TRUNC('month', te.work_date), 'Mon') AS month,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'normal' THEN te.hours_worked ELSE 0 END), 0) AS hours,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'overtime' THEN te.hours_worked ELSE 0 END), 0) AS overtime
                FROM timesheet_entries te
                JOIN employees e ON te.employee_id = e.employee_id
                WHERE e.manager_id = :manager_id
                  AND te.work_date >= CURRENT_DATE - (:months * INTERVAL '1 month')
                  AND te.deleted_at IS NULL
                  AND e.deleted_at IS NULL
                GROUP BY DATE_TRUNC('month', te.work_date)
                ORDER BY DATE_TRUNC('month', te.work_date)
            """),
            {"manager_id": manager_id, "months": months},
        )
        return [
            {
                "month": row["month"],
                "hours": float(row["hours"]),
                "overtime": float(row["overtime"]),
            }
            for row in result.mappings().all()
        ]

    async def get_hours_breakdown(
        self, manager_id: int, start_date: date, end_date: date
    ) -> dict:
        """Get hours breakdown by entry type for manager's team."""
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(SUM(CASE WHEN te.entry_type = 'normal' THEN te.hours_worked ELSE 0 END), 0) AS normal,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'overtime' THEN te.hours_worked ELSE 0 END), 0) AS overtime,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'travel' THEN te.hours_worked ELSE 0 END), 0) AS travel,
                    COALESCE(SUM(CASE WHEN te.entry_type = 'night' THEN te.hours_worked ELSE 0 END), 0) AS night
                FROM timesheet_entries te
                JOIN employees e ON te.employee_id = e.employee_id
                WHERE e.manager_id = :manager_id
                  AND te.work_date BETWEEN :start_date AND :end_date
                  AND te.deleted_at IS NULL
                  AND e.deleted_at IS NULL
            """),
            {"manager_id": manager_id, "start_date": start_date, "end_date": end_date},
        )
        row = result.mappings().one()
        return {
            "normal": float(row["normal"] or 0),
            "overtime": float(row["overtime"] or 0),
            "travel": float(row["travel"] or 0),
            "night": float(row["night"] or 0),
        }
