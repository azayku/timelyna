"""Tests unitaires pour app.utils.period.parse_period."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.utils.period import parse_period


def _today() -> date:
    return date.today()


def test_this_month():
    start, end = parse_period("this_month")
    today = _today()
    assert start == today.replace(day=1)
    assert end == today


def test_last_month():
    start, end = parse_period("last_month")
    today = _today()
    first_this = today.replace(day=1)
    last_month_end = first_this - timedelta(days=1)
    assert start == last_month_end.replace(day=1)
    assert end == last_month_end


def test_quarter():
    start, end = parse_period("quarter")
    today = _today()
    q_start_month = ((today.month - 1) // 3) * 3 + 1
    assert start == today.replace(month=q_start_month, day=1)
    assert end == today


def test_year():
    start, end = parse_period("year")
    today = _today()
    assert start == today.replace(month=1, day=1)
    assert end == today


def test_all():
    start, end = parse_period("all")
    assert start == date(2000, 1, 1)
    assert end == _today()


def test_unknown_falls_back_to_this_month():
    """An unknown period code should fall back to 'this_month' and log a warning."""
    today = _today()
    start, end = parse_period("invalid_period_xyz")
    assert start == today.replace(day=1)
    assert end == today


def test_unknown_logs_warning(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="app.utils.period"):
        parse_period("unknown_value")
    assert any("unknown_value" in rec.message for rec in caplog.records)
