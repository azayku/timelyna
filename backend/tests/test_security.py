"""Unit tests for create_access_token / decode_access_token (task 1.17)."""
from __future__ import annotations

import time

import pytest
from fastapi import HTTPException

from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_roundtrip():
    payload = {"sub": "alice@example.com", "employee_id": 1, "org_id": 1, "role": "employee"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "alice@example.com"
    assert decoded["employee_id"] == 1
    assert decoded["role"] == "employee"


def test_token_contains_exp_and_iat():
    token = create_access_token({"sub": "bob@example.com"})
    decoded = decode_access_token(token)
    assert "exp" in decoded
    assert "iat" in decoded
    assert decoded["exp"] > decoded["iat"]


def test_decode_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not.a.valid.token")
    assert exc_info.value.status_code == 401


def test_decode_tampered_token_raises_401():
    token = create_access_token({"sub": "alice@example.com"})
    tampered = token[:-4] + "XXXX"
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered)
    assert exc_info.value.status_code == 401


def test_role_included_in_payload():
    token = create_access_token({"sub": "mgr@example.com", "role": "manager"})
    decoded = decode_access_token(token)
    assert decoded["role"] == "manager"
