"""Shared period parsing utility — used by ReportingService and FinanceDashboardService."""
from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

_VALID_PERIODS = {"this_month", "last_month", "quarter", "year", "all"}


def parse_period(period: str) -> tuple[date, date]:
    """Convert a period code to a (start_date, end_date) tuple.

    Supported values: ``this_month``, ``last_month``, ``quarter``, ``year``, ``all``.
    Unknown values fall back to ``this_month`` with a warning log.
    """
    today = date.today()

    if period == "this_month":
        return today.replace(day=1), today

    if period == "last_month":
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end

    if period == "quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=q_start_month, day=1), today

    if period == "year":
        return today.replace(month=1, day=1), today

    if period == "all":
        return date(2000, 1, 1), today

    logger.warning("parse_period: valeur inconnue '%s', repli sur 'this_month'", period)
    return today.replace(day=1), today
