"""FinanceDashboardRepository — raw SQL queries for Finance Pro dashboard.

All PostgreSQL-specific SQL is isolated here. The service layer only calls
these methods and never constructs SQL strings directly.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class FinanceDashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_kpis(self, start: date, end: date) -> dict:
        """Aggregate revenue, hours and invoice count for a date range."""
        revenue_row = (
            await self.db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(i.total_amount), 0) AS total_revenue,
                        COALESCE(SUM(i.total_hours), 0)  AS billed_hours,
                        COUNT(i.invoice_id)              AS invoice_count
                    FROM invoices i
                    WHERE i.status IN ('ready', 'sent', 'paid')
                      AND i.created_at::date BETWEEN :start AND :end
                """),
                {"start": start, "end": end},
            )
        ).mappings().one()

        cost_row = (
            await self.db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(te.hours_worked * COALESCE(e.hourly_cost, 0)), 0) AS total_cost
                    FROM timesheet_entries te
                    JOIN employees e ON te.employee_id = e.employee_id
                    WHERE te.status IN ('approved', 'invoiced')
                      AND te.deleted_at IS NULL
                      AND te.work_date BETWEEN :start AND :end
                """),
                {"start": start, "end": end},
            )
        ).mappings().one()

        total_revenue = float(revenue_row["total_revenue"] or 0)
        total_cost = float(cost_row["total_cost"] or 0)
        return {
            "total_revenue": total_revenue,
            "billed_hours": float(revenue_row["billed_hours"] or 0),
            "invoice_count": int(revenue_row["invoice_count"] or 0),
            "gross_margin": total_revenue - total_cost,
        }

    async def get_monthly_revenue(self) -> list[dict]:
        """Revenue per month for the last 12 rolling months."""
        rows = (
            await self.db.execute(
                text("""
                    SELECT
                        TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                        COALESCE(SUM(total_amount), 0)                      AS revenue,
                        COALESCE(SUM(total_hours), 0)                       AS hours
                    FROM invoices
                    WHERE status IN ('ready', 'sent', 'paid')
                      AND created_at >= NOW() - INTERVAL '12 months'
                    GROUP BY DATE_TRUNC('month', created_at)
                    ORDER BY DATE_TRUNC('month', created_at)
                """),
            )
        ).mappings().all()
        return [
            {"month": r["month"], "revenue": float(r["revenue"]), "hours": float(r["hours"])}
            for r in rows
        ]

    async def get_client_revenue(self, start: date, end: date) -> list[dict]:
        """All clients sorted by revenue descending for the period."""
        rows = (
            await self.db.execute(
                text("""
                    SELECT
                        c.client_name,
                        COALESCE(SUM(i.total_amount), 0) AS revenue
                    FROM invoices i
                    JOIN clients c ON i.client_id = c.client_id
                    WHERE i.status IN ('ready', 'sent', 'paid')
                      AND i.created_at::date BETWEEN :start AND :end
                    GROUP BY c.client_id, c.client_name
                    ORDER BY revenue DESC
                """),
                {"start": start, "end": end},
            )
        ).mappings().all()
        return [{"client_name": r["client_name"], "revenue": float(r["revenue"])} for r in rows]

    async def get_burn_rate(self) -> list[dict]:
        """Billed hours vs budget for the top 10 active projects."""
        rows = (
            await self.db.execute(
                text("""
                    SELECT
                        p.project_id,
                        p.project_name,
                        COALESCE(p.budget_hours, 0) AS budget_hours,
                        COALESCE(
                            SUM(CASE WHEN te.status IN ('approved', 'invoiced')
                                THEN te.hours_worked ELSE 0 END),
                            0
                        ) AS billed_hours
                    FROM projects p
                    LEFT JOIN timesheet_entries te
                           ON te.project_id = p.project_id AND te.deleted_at IS NULL
                    WHERE p.deleted_at IS NULL AND p.status = 'active'
                    GROUP BY p.project_id, p.project_name, p.budget_hours
                    ORDER BY billed_hours DESC
                    LIMIT 10
                """),
            )
        ).mappings().all()
        return [
            {
                "project_id": r["project_id"],
                "project_name": r["project_name"],
                "budget_hours": float(r["budget_hours"]),
                "billed_hours": float(r["billed_hours"]),
            }
            for r in rows
        ]

    async def get_recent_invoices(self) -> list[dict]:
        """Last 5 invoices across all statuses."""
        rows = (
            await self.db.execute(
                text("""
                    SELECT
                        i.invoice_id,
                        i.invoice_number,
                        c.client_name,
                        i.total_amount,
                        i.currency,
                        i.status,
                        i.created_at,
                        i.due_date
                    FROM invoices i
                    JOIN clients c ON i.client_id = c.client_id
                    ORDER BY i.created_at DESC
                    LIMIT 5
                """),
            )
        ).mappings().all()
        return [
            {
                "invoice_id": r["invoice_id"],
                "invoice_number": r["invoice_number"],
                "client_name": r["client_name"],
                "total_amount": float(r["total_amount"]),
                "currency": r["currency"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "due_date": str(r["due_date"]) if r["due_date"] else None,
            }
            for r in rows
        ]

    async def get_overdue_invoices(self) -> list[dict]:
        """Invoices with status='sent' whose due_date is in the past."""
        today = date.today()
        rows = (
            await self.db.execute(
                text("""
                    SELECT
                        i.invoice_id,
                        i.invoice_number,
                        c.client_name,
                        i.total_amount,
                        i.currency,
                        i.due_date
                    FROM invoices i
                    JOIN clients c ON i.client_id = c.client_id
                    WHERE i.status = 'sent'
                      AND i.due_date IS NOT NULL
                      AND i.due_date < :today
                    ORDER BY i.due_date ASC
                """),
                {"today": today},
            )
        ).mappings().all()
        return [
            {
                "invoice_id": r["invoice_id"],
                "invoice_number": r["invoice_number"],
                "client_name": r["client_name"],
                "total_amount": float(r["total_amount"]),
                "currency": r["currency"],
                "due_date": str(r["due_date"]),
                "days_overdue": (today - r["due_date"]).days if r["due_date"] else 0,
            }
            for r in rows
        ]
