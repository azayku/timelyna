"""FinanceDashboardService — Finance Pro dashboard aggregations."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.finance_dashboard_repository import FinanceDashboardRepository
from app.utils.period import parse_period


def _prev_period(start: date, end: date) -> tuple[date, date]:
    """Return the equivalent previous period of the same length."""
    delta = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta - 1)
    return prev_start, prev_end


class FinanceDashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = FinanceDashboardRepository(db)

    async def get_dashboard(self, org_id: int, period: str = "this_month") -> dict:
        start, end = parse_period(period)
        prev_start, prev_end = _prev_period(start, end)

        kpis = await self.repo.get_kpis(start, end)
        prev_kpis = await self.repo.get_kpis(prev_start, prev_end)

        # Compute trends
        def trend(curr: float, prev: float) -> float:
            if prev == 0:
                return 0.0
            return round((curr - prev) / prev * 100, 1)

        monthly_revenue = await self.repo.get_monthly_revenue()
        client_revenue_rows = await self.repo.get_client_revenue(start, end)
        burn_rate = await self.repo.get_burn_rate()
        recent_invoices = await self.repo.get_recent_invoices()
        overdue_invoices = await self.repo.get_overdue_invoices()

        # Top 5 clients + "Autres" bucket
        top5 = client_revenue_rows[:5]
        others = sum(r["revenue"] for r in client_revenue_rows[5:])
        if others > 0:
            top5 = [*top5, {"client_name": "Autres", "revenue": others}]
        client_revenue = top5

        return {
            "period": period,
            "start_date": str(start),
            "end_date": str(end),
            "kpis": {
                "total_revenue": kpis["total_revenue"],
                "total_revenue_trend": trend(kpis["total_revenue"], prev_kpis["total_revenue"]),
                "billed_hours": kpis["billed_hours"],
                "billed_hours_trend": trend(kpis["billed_hours"], prev_kpis["billed_hours"]),
                "gross_margin": kpis["gross_margin"],
                "gross_margin_trend": trend(kpis["gross_margin"], prev_kpis["gross_margin"]),
                "invoice_count": kpis["invoice_count"],
                "invoice_count_trend": trend(kpis["invoice_count"], prev_kpis["invoice_count"]),
            },
            "monthly_revenue": monthly_revenue,
            "client_revenue": client_revenue,
            "burn_rate": burn_rate,
            "recent_invoices": recent_invoices,
            "overdue_invoices": overdue_invoices,
        }

