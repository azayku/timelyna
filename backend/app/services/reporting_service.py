"""ReportingService — business logic for reporting & analytics."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.reporting_repository import ReportingRepository
from app.utils.period import parse_period


class ReportingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ReportingRepository(db)

    async def get_personal_stats(self, employee_id: int, period: str = "this_month") -> dict:
        start, end = parse_period(period)
        stats = await self.repo.get_personal_stats(employee_id, start, end)
        project_breakdown = await self.repo.get_project_breakdown(employee_id, start, end)
        task_type_breakdown = await self.repo.get_task_type_breakdown(employee_id, start, end)
        weekly_trend = await self.repo.get_weekly_trend(employee_id, start, end)

        total = stats["total_hours"]
        billable = stats["billable_hours"]
        billable_pct = round((billable / total * 100), 1) if total > 0 else 0.0

        return {
            "period": period,
            "start_date": str(start),
            "end_date": str(end),
            "total_hours": total,
            "billable_hours": billable,
            "billable_pct": billable_pct,
            "days_worked": stats["days_worked"],
            "approved_count": stats["approved_count"],
            "submitted_count": stats["submitted_count"],
            "project_breakdown": project_breakdown,
            "task_type_breakdown": task_type_breakdown,
            "weekly_trend": weekly_trend,
        }

    async def get_team_stats(self, manager_id: int, period: str = "this_month") -> dict:
        start, end = parse_period(period)
        team_rows = await self.repo.get_team_stats(manager_id, start, end)

        team = []
        for row in team_rows:
            total = row["total_hours"]
            billable = row["billable_hours"]
            billable_pct = round((billable / total * 100), 1) if total > 0 else 0.0
            team.append({
                "employee_id": row["employee_id"],
                "name": row["name"],
                "total_hours": total,
                "billable_pct": billable_pct,
                "pending_submissions": row["pending_count"],
            })

        return {
            "period": period,
            "start_date": str(start),
            "end_date": str(end),
            "team": team,
        }

    async def get_manager_dashboard(self, manager_id: int, period: str = "this_month") -> dict:
        """Get dashboard KPIs and monthly trend for manager."""
        start, end = parse_period(period)
        
        # Get team stats for current period
        team_rows = await self.repo.get_team_stats(manager_id, start, end)
        
        # Calculate KPIs
        total_hours = sum(row["total_hours"] for row in team_rows)
        active_employees = len([r for r in team_rows if r["total_hours"] > 0])
        pending_approvals = sum(row["pending_count"] for row in team_rows)
        
        # Calculate overtime (entries with entry_type = 'overtime')
        overtime_hours = await self.repo.get_overtime_hours(manager_id, start, end)
        
        # Get monthly trend (last 9 months)
        monthly_hours = await self.repo.get_monthly_trend(manager_id, months=9)
        
        # Get hours breakdown by entry type
        hours_breakdown = await self.repo.get_hours_breakdown(manager_id, start, end)
        
        return {
            "total_hours_this_month": total_hours,
            "active_employees": active_employees,
            "pending_approvals": pending_approvals,
            "overtime_hours": overtime_hours,
            "monthly_hours": monthly_hours,
            "hours_breakdown": hours_breakdown,
        }

    async def get_hours_report(
        self,
        date_from: date,
        date_to: date,
        employee_id: Optional[int] = None,
        project_id: Optional[int] = None,
        group_by: str = "day",
    ) -> list[dict]:
        return await self.repo.get_hours_report(date_from, date_to, employee_id, project_id, group_by)

    async def get_financial_report(
        self,
        period: str = "this_month",
        client_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> dict:
        start, end = parse_period(period)
        rows = await self.repo.get_financial_report(start, end, client_id=client_id)

        if project_id is not None:
            rows = [r for r in rows if r["project_id"] == project_id]

        return {
            "period": period,
            "start_date": str(start),
            "end_date": str(end),
            "projects": rows,
        }

    # ------------------------------------------------------------------
    # Finance Pro — P&L
    # ------------------------------------------------------------------

    async def get_pnl(self, period: str = "this_month") -> dict:
        start, end = parse_period(period)
        rows = await self.repo.get_financial_report(start, end)

        total_revenue = sum(r["revenue"] for r in rows)
        total_cost = sum(r["internal_cost"] for r in rows)
        gross_margin = total_revenue - total_cost
        gross_margin_pct = round(gross_margin / total_revenue * 100, 1) if total_revenue > 0 else 0.0

        return {
            "period": period,
            "start_date": str(start),
            "end_date": str(end),
            "revenue": total_revenue,
            "costs": total_cost,
            "gross_margin": gross_margin,
            "gross_margin_pct": gross_margin_pct,
            # net_margin = gross_margin (no overhead model yet)
            "net_margin": gross_margin,
            "net_margin_pct": gross_margin_pct,
        }

    # ------------------------------------------------------------------
    # Finance Pro — Project profitability
    # ------------------------------------------------------------------

    async def get_project_profitability(self) -> list[dict]:
        rows = await self.repo.get_project_profitability()
        return rows

    # ------------------------------------------------------------------
    # Finance Pro — Aging report
    # ------------------------------------------------------------------

    async def get_aging_report(self) -> dict:
        return await self.repo.get_aging_report()

    # ------------------------------------------------------------------
    # Finance Pro — Cashflow forecast
    # ------------------------------------------------------------------

    async def get_cashflow_forecast(self, months: int = 3) -> list[dict]:
        return await self.repo.get_cashflow_forecast(months=months)
